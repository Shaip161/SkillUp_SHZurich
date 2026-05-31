'use client'

import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Lightbulb, RotateCcw, Target } from 'lucide-react'
import type {
  CurriculumSkill,
  CurriculumSubskill,
  LearningConcept,
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

function asConcepts(value: unknown): LearningConcept[] {
  return Array.isArray(value) ? (value as LearningConcept[]) : []
}

function paragraphs(value: string): string[] {
  return value
    .split(/\n\n+/)
    .map((part) => part.trim())
    .filter(Boolean)
}

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

  const stagePrompt = typeof stage.context.prompt === 'string' ? stage.context.prompt : ''
  const stageConcepts = asConcepts(stage.context.explained_concepts)
  const conceptSequence = (() => {
    const sequence = asConcepts(stage.context.concept_sequence)
    return sequence.length > 0 ? sequence : stageConcepts
  })()
  const conceptIndex = Math.min(progress.concept_index ?? 0, Math.max(conceptSequence.length - 1, 0))
  const activeConcept = conceptSequence[conceptIndex]
  const explainedConcepts =
    (progress.explained_concepts?.length ?? 0) > 0 ? progress.explained_concepts ?? [] : stageConcepts
  const conceptCheckpoints = Array.isArray(activeConcept?.checkpoints) ? activeConcept.checkpoints : []
  const explanationParagraphs = activeConcept ? paragraphs(activeConcept.explanation) : []
  const exampleParagraphs = activeConcept ? paragraphs(activeConcept.example) : []

  const submitLabel =
    current === 'conceptual'
      ? 'Check my understanding'
      : current === 'practical'
        ? 'Review my approach'
        : 'Complete evaluation'

  const inputPlaceholder =
    current === 'conceptual'
      ? 'Explain the lesson back in your own words, using only what you were taught...'
      : current === 'practical'
        ? 'Describe the approach you would take, the choices you would make, and how you would judge the result...'
        : 'Bring the concept, the approach, and the judgment together in one final response...'

  const submit = () => {
    if (!text.trim()) return
    setPhase('validating')
    setAnimDone(false)
    setApiResult(null)
    submitStage({
      stage: current,
      submission: text,
      attempt: progress.retry_count + 1,
      context: {
        explainedConcepts,
        prompt: stagePrompt || stage.instructions,
        subskillName: subskill.subskill_name,
      },
    }).then(
      setApiResult,
    )
  }

  // ── Non-submission stages ──────────────────────────────────────────────
  if (current === 'introduction') {
    if (!activeConcept) {
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
            Continue
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Button>
        </StageShell>
      )
    }

    const totalConcepts = conceptSequence.length

    return (
      <StageShell stage={stage} icon={<Lightbulb className="h-4 w-4 text-primary" />}>
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(280px,0.9fr)] lg:items-start">
          <article className="space-y-5">
            <div>
              <h3 className="font-display text-3xl font-semibold tracking-tight text-white sm:text-[2.1rem]">
                {activeConcept.title}
              </h3>
            </div>

            <div className="space-y-4 text-[15px] leading-8 text-white/76 sm:text-base">
              {explanationParagraphs.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </article>

          <aside className="space-y-4 lg:sticky lg:top-24">
            <div className="rounded-3xl border border-white/8 bg-white/[0.03] p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/35">In practice</p>
              <div className="mt-3 space-y-3 text-sm leading-7 text-white/70">
                {exampleParagraphs.map((paragraph) => (
                  <p key={paragraph}>{paragraph}</p>
                ))}
              </div>
            </div>

            <div className="rounded-3xl border border-primary/18 bg-primary/[0.06] p-5">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary/80">
                How to think about it
              </p>
              {activeConcept.intuition && (
                <p className="mt-3 text-sm leading-7 text-white/78">{activeConcept.intuition}</p>
              )}

              {conceptCheckpoints.length > 0 && (
                <ul className="mt-4 space-y-2.5">
                  {conceptCheckpoints.map((item) => (
                    <li key={item} className="flex items-start gap-2.5 text-sm leading-6 text-white/76">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      {item}
                    </li>
                  ))}
                </ul>
              )}

              <div className="mt-5 border-t border-white/10 pt-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/35">Remember</p>
                <p className="mt-2 text-sm leading-7 text-white/80">{activeConcept.takeaway}</p>
              </div>
            </div>
          </aside>
        </div>

        <div className="mt-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2" aria-hidden="true">
            {conceptSequence.map((concept, index) => {
              const active = index === conceptIndex
              const complete = index < conceptIndex

              return (
                <span
                  key={concept.concept_id}
                  className={`h-2 rounded-full transition-all ${
                    active ? 'w-8 bg-primary' : complete ? 'w-2 bg-white/55' : 'w-2 bg-white/15'
                  }`}
                />
              )
            })}
          </div>

          <Button className="group" onClick={() => advance(skill.skill_id, subskill.subskill_id, 'introduction')}>
            {conceptIndex < totalConcepts - 1 ? 'Next lesson' : 'Move to understanding'}
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
          </Button>
        </div>
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
            <p className="mb-4 max-w-3xl text-sm leading-6 text-white/52">
              Focus on {stage.rubric.join(' · ').toLowerCase()}.
            </p>
          )}
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={current === 'conceptual' ? 8 : 10}
            placeholder={isCode ? inputPlaceholder : inputPlaceholder}
            className={`w-full resize-y rounded-2xl border border-white/12 bg-base-900/60 p-5 text-[15px] leading-7 text-white placeholder:text-white/25 focus:border-primary/50 focus:outline-none ${
              isCode ? 'font-mono text-sm leading-7' : ''
            }`}
          />
          <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-xs text-white/30">
              {text.trim().split(/\s+/).filter(Boolean).length} words
            </span>
            <Button onClick={submit} disabled={!text.trim()}>
              {submitLabel}
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
      className="glass rounded-[32px] p-6 sm:p-8 lg:p-10"
    >
      <div className="mb-1 flex items-center gap-2">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-white/5 ring-1 ring-white/10">
          {icon}
        </span>
        <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-white/40">
          {stage.title}
        </span>
      </div>
      <p className="mt-4 max-w-3xl text-[15px] leading-8 text-white/72">{stage.instructions}</p>
      <div className="mt-7">{children}</div>
    </motion.div>
  )
}
