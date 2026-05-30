'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { MatchResponse } from '@/lib/types'
import { JobCard } from '@/components/JobCard'

function SkeletonCard() {
  return (
    <div className="animate-pulse space-y-4 rounded-2xl border border-white/10 bg-white/5 p-5">
      <div className="space-y-2">
        <div className="h-5 w-3/4 rounded bg-white/10" />
        <div className="h-4 w-1/2 rounded bg-white/10" />
      </div>
      <div className="flex gap-3">
        <div className="h-3.5 w-16 rounded bg-white/10" />
        <div className="h-3.5 w-24 rounded bg-white/10" />
      </div>
      <div className="h-1.5 w-full rounded-full bg-white/10" />
      <div className="flex flex-wrap gap-1.5">
        {[72, 56, 88, 64].map((w) => (
          <div key={w} className="h-5 rounded-full bg-white/10" style={{ width: w }} />
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
      router.replace('/')
      return
    }
    try {
      setData(JSON.parse(raw) as MatchResponse)
    } catch {
      router.replace('/')
      return
    }
    setReady(true)
  }, [router])

  if (!ready) {
    return (
      <div className="space-y-8">
        <div className="space-y-2">
          <div className="h-7 w-64 animate-pulse rounded-lg bg-white/10" />
          <div className="h-4 w-80 animate-pulse rounded bg-white/10" />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {[...Array(4)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      </div>
    )
  }

  const sorted = [...(data?.matches ?? [])].sort((a, b) => b.score - a.score)
  const userId = data?.user_id ?? ''
  const count = sorted.length

  return (
    <div className="space-y-8">
      {/* Heading */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          {count === 0
            ? 'No matches found for your CV'
            : `${count} match${count === 1 ? '' : 'es'} found for your CV`}
        </h1>
        <p className="mt-1 text-sm text-white/40">
          Sorted by relevance — click any card to see the full job and skill gap.
        </p>
      </div>

      {/* Empty state */}
      {count === 0 ? (
        <div className="flex flex-col items-center gap-4 rounded-2xl border border-white/10 bg-white/5 py-16 text-center">
          <p className="text-white/50">
            We couldn&apos;t find jobs with a similarity score above 50%.
          </p>
          <button
            onClick={() => router.push('/')}
            className="rounded-lg bg-white/10 px-5 py-2 text-sm font-medium text-white hover:bg-white/20 transition-colors"
          >
            Try a different CV
          </button>
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {sorted.map((match) => (
            <JobCard key={match.job.id} match={match} userId={userId} />
          ))}
        </div>
      )}
    </div>
  )
}
