'use client'

import { createContext, useContext, useEffect, useMemo, useReducer, useState } from 'react'
import type {
  Curriculum,
  CurriculumSkill,
  MasteryStatus,
  StageEvaluation,
  StageType,
  SubskillProgress,
  TargetRole,
} from '@/lib/types'

/**
 * The journey store: the user's chosen target, the generated curriculum, and
 * per-subskill progress. Persisted to localStorage so progress survives reloads
 * (the spec's "progress persistence"). Server data (generation/evaluation) comes
 * from the route handlers; progression state is owned here.
 */
export interface SelectedTarget {
  jobId: string
  title: string
  industry: string
  compatibility: number
}

interface JourneyState {
  target: SelectedTarget | null
  targetRole: TargetRole | null
  curriculum: Curriculum | null
  progress: Record<string, SubskillProgress> // keyed by subskill_id
}

type Action =
  | { type: 'SELECT_TARGET'; target: SelectedTarget; targetRole: TargetRole }
  | { type: 'SET_CURRICULUM'; curriculum: Curriculum }
  | { type: 'ADVANCE'; skillId: string; subskillId: string; from: StageType }
  | { type: 'APPLY_EVALUATION'; skillId: string; subskillId: string; ev: StageEvaluation }
  | { type: 'RESET' }
  | { type: 'HYDRATE'; state: JourneyState }

const STANDARD: StageType[] = ['introduction', 'conceptual', 'practical', 'evaluation']
const KEY = 'ascend.journey'

const empty: JourneyState = { target: null, targetRole: null, curriculum: null, progress: {} }

function freshProgress(skillId: string, subskillId: string): SubskillProgress {
  return {
    skill_id: skillId,
    subskill_id: subskillId,
    completed_steps: [],
    current_stage: 'introduction',
    mastery_status: 'in_progress',
    progress_percent: 0,
    retry_count: 0,
    latest_scores: {},
  }
}

function percent(completed: StageType[], mastery: MasteryStatus): number {
  if (mastery === 'completed') return 100
  const done = STANDARD.filter((s) => completed.includes(s)).length
  return Math.round((done / STANDARD.length) * 100)
}

function seedProgress(curriculum: Curriculum): Record<string, SubskillProgress> {
  const progress: Record<string, SubskillProgress> = {}
  for (const skill of curriculum.skills) {
    skill.subskills.forEach((sub, i) => {
      progress[sub.subskill_id] = {
        ...freshProgress(skill.skill_id, sub.subskill_id),
        // First subskill of each skill starts active; rest are not_started (locked).
        mastery_status: i === 0 ? 'in_progress' : 'not_started',
        current_stage: i === 0 ? 'introduction' : null,
      }
    })
  }
  return progress
}

function reducer(state: JourneyState, action: Action): JourneyState {
  switch (action.type) {
    case 'HYDRATE':
      return action.state
    case 'SELECT_TARGET':
      return { ...empty, target: action.target, targetRole: action.targetRole }
    case 'SET_CURRICULUM':
      return { ...state, curriculum: action.curriculum, progress: seedProgress(action.curriculum) }
    case 'ADVANCE': {
      // For non-submission stages (introduction, reflection -> retry).
      const p = state.progress[action.subskillId]
      if (!p) return state
      let completed: StageType[] = p.completed_steps
      let next: StageType | null = p.current_stage
      let mastery: MasteryStatus = p.mastery_status
      if (action.from === 'introduction') {
        completed = Array.from(new Set<StageType>([...completed, 'introduction']))
        next = 'conceptual'
        mastery = 'in_progress'
      } else if (action.from === 'reflection') {
        next = 'evaluation'
        mastery = 'retry_ready'
      }
      return {
        ...state,
        progress: {
          ...state.progress,
          [action.subskillId]: {
            ...p,
            completed_steps: completed,
            current_stage: next,
            mastery_status: mastery,
            progress_percent: percent(completed, mastery),
          },
        },
      }
    }
    case 'APPLY_EVALUATION': {
      const p = state.progress[action.subskillId]
      if (!p) return state
      const { ev } = action
      const scoreKey =
        ev.stage === 'conceptual'
          ? 'conceptual'
          : ev.stage === 'practical'
            ? 'practical'
            : 'final'
      const completed = ev.passed
        ? Array.from(new Set([...p.completed_steps, ev.stage]))
        : p.completed_steps
      const updated: SubskillProgress = {
        ...p,
        completed_steps: completed,
        current_stage: ev.next_stage,
        mastery_status: ev.mastery_status,
        latest_scores: { ...p.latest_scores, [scoreKey]: ev.score },
        retry_count: ev.stage === 'evaluation' && !ev.passed ? p.retry_count + 1 : p.retry_count,
        progress_percent: percent(completed, ev.mastery_status),
      }
      const nextProgress = { ...state.progress, [action.subskillId]: updated }

      // On mastery, unlock the next subskill in the same skill.
      if (ev.mastery_status === 'completed' && state.curriculum) {
        const skill = state.curriculum.skills.find((s) => s.skill_id === action.skillId)
        if (skill) {
          const idx = skill.subskills.findIndex((s) => s.subskill_id === action.subskillId)
          const nextSub = skill.subskills[idx + 1]
          if (nextSub && nextProgress[nextSub.subskill_id]?.mastery_status === 'not_started') {
            nextProgress[nextSub.subskill_id] = {
              ...nextProgress[nextSub.subskill_id],
              mastery_status: 'in_progress',
              current_stage: 'introduction',
            }
          }
        }
      }
      return { ...state, progress: nextProgress }
    }
    case 'RESET':
      return empty
    default:
      return state
  }
}

interface JourneyContextValue {
  state: JourneyState
  ready: boolean
  selectTarget: (target: SelectedTarget, targetRole: TargetRole) => void
  setCurriculum: (c: Curriculum) => void
  advance: (skillId: string, subskillId: string, from: StageType) => void
  applyEvaluation: (skillId: string, subskillId: string, ev: StageEvaluation) => void
  reset: () => void
}

const JourneyContext = createContext<JourneyContextValue | null>(null)

export function JourneyProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = useReducer(reducer, empty)
  const [ready, setReady] = useState(false)

  // Load persisted journey once.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY)
      if (raw) dispatch({ type: 'HYDRATE', state: JSON.parse(raw) as JourneyState })
    } catch {
      /* ignore */
    }
    setReady(true)
  }, [])

  // Persist on change (after hydration).
  useEffect(() => {
    if (!ready) return
    try {
      localStorage.setItem(KEY, JSON.stringify(state))
    } catch {
      /* ignore */
    }
  }, [state, ready])

  const value = useMemo<JourneyContextValue>(
    () => ({
      state,
      ready,
      selectTarget: (target, targetRole) => dispatch({ type: 'SELECT_TARGET', target, targetRole }),
      setCurriculum: (curriculum) => dispatch({ type: 'SET_CURRICULUM', curriculum }),
      advance: (skillId, subskillId, from) => dispatch({ type: 'ADVANCE', skillId, subskillId, from }),
      applyEvaluation: (skillId, subskillId, ev) =>
        dispatch({ type: 'APPLY_EVALUATION', skillId, subskillId, ev }),
      reset: () => dispatch({ type: 'RESET' }),
    }),
    [state, ready],
  )

  return <JourneyContext.Provider value={value}>{children}</JourneyContext.Provider>
}

export function useJourney(): JourneyContextValue {
  const ctx = useContext(JourneyContext)
  if (!ctx) throw new Error('useJourney must be used within <JourneyProvider>')
  return ctx
}

// ───────────────────────────── derived selectors ─────────────────────────────

export function skillProgress(skill: CurriculumSkill, progress: Record<string, SubskillProgress>): number {
  if (skill.subskills.length === 0) return 0
  const completed = skill.subskills.filter(
    (s) => progress[s.subskill_id]?.mastery_status === 'completed',
  ).length
  return completed / skill.subskills.length
}

export function overallProgress(
  curriculum: Curriculum | null,
  progress: Record<string, SubskillProgress>,
): number {
  if (!curriculum) return 0
  const all = curriculum.skills.flatMap((s) => s.subskills)
  if (all.length === 0) return 0
  const done = all.filter((s) => progress[s.subskill_id]?.mastery_status === 'completed').length
  return done / all.length
}

export function isSubskillUnlocked(
  skill: CurriculumSkill,
  subskillId: string,
  progress: Record<string, SubskillProgress>,
): boolean {
  const status = progress[subskillId]?.mastery_status
  return status !== undefined && status !== 'not_started'
}
