'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { MatchResponse } from '@/lib/types'
import { TargetJobCard } from '@/components/job/TargetJobCard'
import { Stagger } from '@/components/ui/motion'
import { Skeleton } from '@/components/ui/Skeleton'
import { Button } from '@/components/ui/Button'

function LoadingGrid() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <Skeleton className="h-8 w-72" />
        <Skeleton className="h-4 w-96" />
      </div>
      <div className="grid gap-5 sm:grid-cols-2">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-56 rounded-3xl" />
        ))}
      </div>
    </div>
  )
}

export default function MatchesPage() {
  const router = useRouter()
  const [data, setData] = useState<MatchResponse | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    const raw = sessionStorage.getItem('matchResponse')
    if (!raw) {
      router.replace('/upload')
      return
    }
    try {
      setData(JSON.parse(raw) as MatchResponse)
    } catch {
      router.replace('/upload')
      return
    }
    setReady(true)
  }, [router])

  if (!ready) return <LoadingGrid />

  const sorted = [...(data?.matches ?? [])].sort((a, b) => b.score - a.score)
  const userId = data?.user_id ?? ''

  return (
    <div className="space-y-8">
      <div>
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-primary/70">
          Step 2 · Choose a future self
        </p>
        <h1 className="mt-3 font-display text-4xl font-bold tracking-tight">
          {sorted.length === 0 ? 'No clear matches yet' : 'Where you could go next'}
        </h1>
        <p className="mt-2 max-w-xl text-white/55">
          {sorted.length === 0
            ? "We couldn't find roles above the match threshold. Try a different CV."
            : 'Each role is a version of you within reach. Pick one to see the exact path there.'}
        </p>
      </div>

      {sorted.length === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-3xl border border-white/10 bg-white/[0.03] py-16 text-center">
          <p className="text-white/50">No roles matched above 50% similarity.</p>
          <Button variant="secondary" onClick={() => router.push('/upload')}>
            Try a different CV
          </Button>
        </div>
      ) : (
        <Stagger className="grid gap-5 sm:grid-cols-2" stagger={0.08}>
          {sorted.map((match, i) => (
            <TargetJobCard key={match.job.id} match={match} userId={userId} index={i} />
          ))}
        </Stagger>
      )}
    </div>
  )
}
