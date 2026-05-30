'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Lightbulb, RotateCcw, Target } from 'lucide-react'
import type {
  CurriculumSkill,
  CurriculumSubskill,
  StageEvaluation,
  StagePayload,
  StageType,
  SubskillProgress,
} from '@/lib/types'
import { submitStage } from '@/lib/api'
import { useJourney } from '@/lib/store/journey'
import { Button } from '@/components/ui/Button'
import { ValidationOverlay } from './ValidationOverlay'
import { EvaluationResultCard } from './EvaluationResultCard'

type Phase = 'input' | 'validating' | 'result'

/** Drives one subskill through intro → conceptual → practical → evaluation → reflection. */
export function StageFlow({
  skill,
  subskill,
  progress,
}: {
  skill: CurriculumSkill
  subskill: CurriculumSubskill
  progress: SubskillProgress
}) {
  const { advance, applyEvaluation } = useJourney()
  const current = progress.current_stage

  const stage: StagePayload | undefined = useMemo(
    () => subskill.stages.find((s) => s.stage_type === current),
    [subskill.stages, current],
  )

  const [text, setText] = useState('')
  const [phase, setPhase] = useState<Phase>('input')
  const [apiResult, setApiResult] = useState<StageEvaluation | null>(null)
  const [animDone, setAnimDone] = useState(false)
  const [lastEval, setLastEval] = useState<StageEvaluation | null>(null)

  // Reset interaction state whenever the active stage changes.
  useEffect(() => {
    setText('')
    setPhase('input')
    setApiResult(null)
    setAnimDone(false)
    setLastEval(null)
  }, [current])

  // Reveal the result once both the validation animation and the API are done.
  useEffect(() => {
    if (phase === 'validating' && animDone && apiResult) {
      setLastEval(apiResult)
      setPhase('result')
    }
  }, [phase, animDone, apiResult])

  if (!current || !stage) return null

  const submit = () => {
    if (!text.trim()) return
    setPhase('validating')
    setAnimDone(false)
    setApiResult(null)
    submitStage({ stage: current, submission: text, attempt: progress.retry_count + 1 }).then(
      setApiResult,
    )
  }

  // ── Non-submission stages ──────────────────────────────────────────────
  if (current === 'introduction') {
    return (
      <StageShell stage={stage} icon={<Lightbulb className="h-4 w-4 text-primary" />}>
        <ul className="space-y-2">
          {stage.rubric.map((r) => (
            <li key={r} className="flex items-start gap-2 text-sm text-white/65">
              <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
              {r}
            </li>
          ))}
        </ul>
        <Button className="mt-6 group" onClick={() => advance(skill.skill_id, subskill.subskill_id, 'introduction')}>
          I understand — continue
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </Button>
      </StageShell>
    )
  }

  if (current === 'reflection') {
    return (
      <StageShell stage={stage} icon={<RotateCcw className="h-4 w-4 text-amber-300" />}>
        <div className="rounded-xl border border-amber-400/20 bg-amber-400/[0.04] p-4 text-sm text-white/70">
          {progress.latest_scores.final !== undefined && (
            <p className="mb-2">
              Last evaluation scored{' '}
              <span className="font-semibold text-amber-200">
                {Math.round((progress.latest_scores.final ?? 0) * 100)}%
              </span>
              . Focus your retry on demonstrating the concept inside a concrete workflow.
            </p>
          )}
          <p>{stage.instructions}</p>
        </div>
        <Button className="mt-6" onClick={() => advance(skill.skill_id, subskill.subskill_id, 'reflection')}>
          Retry the evaluation
        </Button>
      </StageShell>
    )
  }

  // ── Submission stages: conceptual / practical / evaluation ─────────────
  const isCode = current === 'practical'
  return (
    <StageShell stage={stage} icon={<Target className="h-4 w-4 text-accent" />}>
      {phase === 'input' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {stage.rubric.length > 0 && (
            <div className="mb-4 rounded-xl border border-white/8 bg-white/[0.02] p-3">
              <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wider text-white/35">
                What we&apos;re looking for
              </p>
              <ul className="space-y-1">
                {stage.rubric.map((r) => (
                  <li key={r} className="text-sm text-white/55">
                    · {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={isCode ? 10 : 6}
            placeholder={isCode ? '// Implement your solution or describe your workflow…' : 'Type your answer…'}
            className={`w-full resize-y rounded-xl border border-white/12 bg-base-900/60 p-4 text-sm text-white placeholder:text-white/25 focus:border-primary/50 focus:outline-none ${
              isCode ? 'font-mono' : ''
            }`}
          />
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-white/30">
              {text.trim().split(/\s+/).filter(Boolean).length} words
            </span>
            <Button onClick={submit} disabled={!text.trim()}>
              Submit for validation
            </Button>
          </div>
        </motion.div>
      )}

      {phase === 'validating' && <ValidationOverlay onDone={() => setAnimDone(true)} />}

      {phase === 'result' && lastEval && (
        <EvaluationResultCard
          ev={lastEval}
          continueLabel={current === 'evaluation' ? 'Complete milestone' : 'Continue'}
          onContinue={() => applyEvaluation(skill.skill_id, subskill.subskill_id, lastEval)}
          onRetry={() => {
            // Persist the attempt; for evaluation this routes into reflection.
            if (current === 'evaluation') {
              applyEvaluation(skill.skill_id, subskill.subskill_id, lastEval)
            } else {
              setPhase('input')
              setText('')
            }
          }}
        />
      )}
    </StageShell>
  )
}

/** Shared chrome for a stage: title, type chip, instructions, then children. */
function StageShell({
  stage,
  icon,
  children,
}: {
  stage: StagePayload
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <motion.div
      key={stage.stage_id}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
      className="glass rounded-3xl p-6 sm:p-8"
    >
      <div className="mb-1 flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-white/5 ring-1 ring-white/10">
          {icon}
        </span>
        <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/40">
          {stage.title}
        </span>
      </div>
      <p className="mt-3 text-[15px] leading-relaxed text-white/75">{stage.instructions}</p>
      <div className="mt-6">{children}</div>
    </motion.div>
  )
}
