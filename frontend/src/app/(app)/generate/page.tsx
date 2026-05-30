'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { generateCurriculum } from '@/lib/api'
import { useJourney } from '@/lib/store/journey'
import type { Curriculum, TargetRole } from '@/lib/types'
import { GenerationSequence } from '@/components/learning/GenerationSequence'
import { Button } from '@/components/ui/Button'

interface GenInput {
  targetRole: TargetRole
  missingSkills: string[]
  userProfile?: Record<string, unknown>
}

export default function GeneratePage() {
  const router = useRouter()
  const { state, setCurriculum } = useJourney()
  const [curriculum, setLocalCurriculum] = useState<Curriculum | null>(null)
  const [error, setError] = useState<string | null>(null)
  const startedRef = useRef(false)

  const targetTitle = state.targetRole?.title ?? 'your target role'

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true

    const raw = sessionStorage.getItem('generationInput')
    if (!raw) {
      router.replace('/matches')
      return
    }
    const input = JSON.parse(raw) as GenInput

    generateCurriculum({
      targetRole: input.targetRole,
      missingSkills: input.missingSkills,
      userProfile: input.userProfile,
    })
      .then((c) => setLocalCurriculum(c))
      .catch((e) => setError(e instanceof Error ? e.message : 'Generation failed'))
  }, [router])

  const handleComplete = useCallback(() => {
    if (curriculum) {
      setCurriculum(curriculum)
      router.replace('/roadmap')
    }
  }, [curriculum, setCurriculum, router])

  if (error) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
        <p className="text-white/60">Couldn&apos;t generate your path: {error}</p>
        <Button variant="secondary" onClick={() => router.push('/matches')}>
          Back to matches
        </Button>
      </div>
    )
  }

  return (
    <GenerationSequence ready={!!curriculum} onComplete={handleComplete} targetTitle={targetTitle} />
  )
}
