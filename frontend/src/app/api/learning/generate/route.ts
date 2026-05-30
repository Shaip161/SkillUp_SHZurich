import { NextResponse } from 'next/server'
import { buildMockCurriculum } from '@/lib/learning/mock-curriculum'
import type { TargetRole } from '@/lib/types'

/**
 * POST /api/learning/generate
 * Mock System B curriculum generation. Body: { targetRole, missingSkills, userProfile?, curriculumId? }.
 * Returns a contract-shaped curriculum after a short simulated "generation" delay.
 *
 * Swap `buildMockCurriculum` for a fetch to the real System B service to go live.
 */
export async function POST(req: Request) {
  let body: {
    targetRole?: TargetRole
    missingSkills?: string[]
    userProfile?: Record<string, unknown>
    curriculumId?: string
  }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 })
  }

  const targetRole = body.targetRole
  if (!targetRole?.title) {
    return NextResponse.json({ error: 'targetRole.title is required' }, { status: 422 })
  }

  // Simulate the intelligence-engine latency that powers the cinematic screen.
  await new Promise((r) => setTimeout(r, 600))

  const curriculum = buildMockCurriculum({
    targetRole,
    missingSkills: body.missingSkills ?? [],
    userProfile: body.userProfile ?? {},
    curriculumId: body.curriculumId,
  })

  return NextResponse.json(curriculum)
}
