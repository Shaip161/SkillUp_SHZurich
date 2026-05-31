import { NextResponse } from 'next/server'
import type { LearningConcept, MasteryStatus, StageEvaluation, StageType } from '@/lib/types'

/**
 * POST /api/learning/stage/submit
 * Mock evaluation for conceptual / practical / evaluation stages. Mirrors System
 * B's runtime evaluators: a heuristic score, pass/fail, errors, feedback, and the
 * next stage. Body: { stage, submission, attempt? }.
 *
 * The heuristic rewards substantive answers so the demo is deterministic yet
 * forgiving; a too-short answer fails and routes into the remediation loop.
 */
const NEXT: Record<StageType, StageType | null> = {
  introduction: 'conceptual',
  conceptual: 'practical',
  practical: 'evaluation',
  evaluation: null,
  reflection: 'evaluation',
}

const STOPWORDS = new Set([
  'about',
  'after',
  'before',
  'because',
  'build',
  'checks',
  'concept',
  'inside',
  'means',
  'quality',
  'sequence',
  'should',
  'their',
  'there',
  'these',
  'using',
  'with',
])

function conceptFocus(concepts: LearningConcept[]): string {
  if (concepts.length === 0) return 'the taught material'
  return concepts.map((concept) => concept.title).join(', ')
}

function conceptCoverageBonus(text: string, concepts: LearningConcept[]): number {
  if (concepts.length === 0) return 0
  const haystack = text.toLowerCase()
  const keywords = Array.from(
    new Set(
      concepts
        .flatMap((concept) => `${concept.title} ${concept.takeaway}`.toLowerCase().match(/[a-z]+/g) ?? [])
        .filter((token) => token.length > 4 && !STOPWORDS.has(token)),
    ),
  ).slice(0, 10)

  if (keywords.length === 0) return 0

  const hits = keywords.filter((token) => haystack.includes(token)).length
  return Math.min(0.18, (hits / Math.min(keywords.length, 4)) * 0.18)
}

function scoreSubmission(stage: StageType, text: string, concepts: LearningConcept[]): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length
  const base = Math.min(1, words / 28)
  const structure = /\b(step|trigger|because|so that|first|then|validate|check)\b/i.test(text)
    ? 0.12
    : 0
  const context = conceptCoverageBonus(text, concepts)
  const stageWeight = stage === 'conceptual' ? 0.8 : stage === 'practical' ? 0.85 : 0.9
  const raw = Math.min(1, base * stageWeight + structure + context)
  return Math.round(raw * 100) / 100
}

function remediationHint(stage: StageType, concepts: LearningConcept[]): string {
  const focus = conceptFocus(concepts)
  if (stage === 'conceptual') {
    return `Anchor your explanation in the concepts that were actually taught: ${focus}.`
  }
  if (stage === 'practical') {
    return `Use the taught concepts to describe a concrete approach and validation plan: ${focus}.`
  }
  return `Synthesize the full teaching sequence into one coherent answer: ${focus}.`
}

export async function POST(req: Request) {
  let body: {
    stage?: StageType
    submission?: string
    attempt?: number
    context?: {
      explainedConcepts?: LearningConcept[]
      prompt?: string
      subskillName?: string
    }
  }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const stage = body.stage
  if (!stage) return NextResponse.json({ error: 'stage is required' }, { status: 422 })

  await new Promise((r) => setTimeout(r, 500))

  const text = body.submission ?? ''
  const explainedConcepts = Array.isArray(body.context?.explainedConcepts)
    ? body.context?.explainedConcepts
    : []
  const score = scoreSubmission(stage, text, explainedConcepts)
  const threshold = stage === 'conceptual' ? 0.62 : stage === 'practical' ? 0.68 : 0.72
  const passed = score >= threshold

  const errors = passed
    ? []
    : [
        text.trim().length < 12
          ? 'Answer is too brief to demonstrate what you learned from the teaching sequence.'
          : remediationHint(stage, explainedConcepts),
      ]

  const masteryStatus: MasteryStatus =
    stage === 'evaluation' ? (passed ? 'completed' : 'needs_remediation') : 'in_progress'

  const evaluation: StageEvaluation = {
    stage,
    score,
    passed,
    errors,
    feedback: passed
      ? explainedConcepts.length > 0
        ? `Strong work. Your answer stayed grounded in the taught concepts: ${conceptFocus(explainedConcepts)}.`
        : 'Strong work. Clear reasoning and solid execution.'
      : 'Not quite yet. Reconnect your answer to the concepts that were already taught, then retry.',
    retry_required: stage === 'evaluation' && !passed,
    next_stage: passed ? NEXT[stage] : stage === 'evaluation' ? 'reflection' : stage,
    mastery_status: masteryStatus,
  }

  return NextResponse.json(evaluation)
}
