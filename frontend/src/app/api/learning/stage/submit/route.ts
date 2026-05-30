import { NextResponse } from 'next/server'
import type { StageEvaluation, StageType, MasteryStatus } from '@/lib/types'

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

function scoreSubmission(stage: StageType, text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length
  // Saturating score: ~25 words reaches a strong answer.
  const base = Math.min(1, words / 25)
  // Reward structure/keywords lightly for practical/evaluation stages.
  const structure = /\b(step|trigger|because|so that|first|then|validate|check)\b/i.test(text)
    ? 0.12
    : 0
  const raw = Math.min(1, base * 0.9 + structure)
  return Math.round(raw * 100) / 100
}

export async function POST(req: Request) {
  let body: { stage?: StageType; submission?: string; attempt?: number }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const stage = body.stage
  if (!stage) return NextResponse.json({ error: 'stage is required' }, { status: 422 })

  await new Promise((r) => setTimeout(r, 500))

  const text = body.submission ?? ''
  const score = scoreSubmission(stage, text)
  const threshold = stage === 'practical' ? 0.7 : 0.72
  const passed = score >= threshold

  const errors = passed
    ? []
    : [
        text.trim().length < 12
          ? 'Answer is too brief to demonstrate understanding.'
          : 'Reasoning is incomplete — connect the concept to a concrete workflow.',
      ]

  const masteryStatus: MasteryStatus =
    stage === 'evaluation' ? (passed ? 'completed' : 'needs_remediation') : 'in_progress'

  const evaluation: StageEvaluation = {
    stage,
    score,
    passed,
    errors,
    feedback: passed
      ? 'Strong work — clear reasoning and solid execution.'
      : 'Not quite yet. Strengthen the weak points below, then retry.',
    retry_required: stage === 'evaluation' && !passed,
    next_stage: passed ? NEXT[stage] : stage === 'evaluation' ? 'reflection' : stage,
    mastery_status: masteryStatus,
  }

  return NextResponse.json(evaluation)
}
