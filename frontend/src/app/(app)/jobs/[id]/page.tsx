'use client'

import { Suspense, useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, MapPin, Sparkles, Tag } from 'lucide-react'
import type { GapResponse, JobDetail } from '@/lib/types'
import { getJob, getSkillGap } from '@/lib/api'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { SkillGapViz } from '@/components/job/SkillGapViz'
import { useJourney } from '@/lib/store/journey'
import { slugify } from '@/lib/utils'

function getVariant(skill: string, gap: GapResponse | null): 'matched' | 'missing' | 'neutral' {
  if (!gap) return 'neutral'
  const lower = skill.toLowerCase()
  if (gap.matched_skills.some((m) => m.toLowerCase() === lower)) return 'matched'
  if (gap.missing_skills.some((m) => m.toLowerCase() === lower)) return 'missing'
  return 'neutral'
}

function DetailSkeleton() {
  return (
    <div className="mx-auto max-w-3xl space-y-8">
      <Skeleton className="h-4 w-28" />
      <Skeleton className="h-10 w-3/4" />
      <Skeleton className="h-24 w-full rounded-2xl" />
      <Skeleton className="h-40 w-full rounded-2xl" />
    </div>
  )
}

function JobDetailContent() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
  const { selectTarget } = useJourney()
  const jobId = params.id as string
  const userId = searchParams.get('user_id') ?? ''

  const [job, setJob] = useState<JobDetail | null>(null)
  const [gap, setGap] = useState<GapResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const [jobData, gapData] = await Promise.all([
          getJob(jobId),
          userId ? getSkillGap(jobId, userId) : Promise.resolve(null),
        ])
        setJob(jobData)
        setGap(gapData)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load role details')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jobId, userId])

  if (loading) return <DetailSkeleton />

  if (error || !job) {
    return (
      <div className="space-y-4 py-16 text-center">
        <p className="text-white/50">{error ?? 'Role not found.'}</p>
        <Button variant="ghost" onClick={() => router.push('/matches')}>
          Back to matches
        </Button>
      </div>
    )
  }

  function startGeneration() {
    if (!job) return
    const targetRole = {
      role_id: slugify(job.title),
      title: job.title,
      industry: job.category ?? 'General',
    }
    const missingSkills = gap?.missing_skills ?? job.required_skills
    selectTarget(
      { jobId: job.id, title: job.title, industry: targetRole.industry, compatibility: 0 },
      targetRole,
    )
    sessionStorage.setItem(
      'generationInput',
      JSON.stringify({ targetRole, missingSkills, userProfile: { user_id: userId } }),
    )
    router.push('/generate')
  }

  return (
    <div className="mx-auto max-w-3xl space-y-10">
      <button
        onClick={() => router.push('/matches')}
        className="flex items-center gap-1.5 text-sm text-white/40 transition-colors hover:text-white/70"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to matches
      </button>

      {/* Header */}
      <div className="flex items-start justify-between gap-6">
        <div className="space-y-2">
          <h1 className="font-display text-3xl font-bold leading-tight">{job.title}</h1>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-white/50">
            {job.company && <span>{job.company}</span>}
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3.5 w-3.5" />
                {job.location}
              </span>
            )}
            {job.category && (
              <span className="flex items-center gap-1">
                <Tag className="h-3.5 w-3.5" />
                {job.category}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Description */}
      <section className="space-y-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-white/40">About the role</h2>
        <p className="whitespace-pre-line text-sm leading-relaxed text-white/60">{job.description}</p>
      </section>

      {/* Required skills */}
      {job.required_skills.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-white/40">
            What the role asks for
          </h2>
          <div className="flex flex-wrap gap-1.5">
            {job.required_skills.map((s) => (
              <Badge key={s} variant={getVariant(s, gap)}>
                {s}
              </Badge>
            ))}
          </div>
        </section>
      )}

      {/* Trajectory / gap */}
      {gap && (
        <section className="glass rounded-3xl p-6">
          <SkillGapViz gap={gap} />
        </section>
      )}

      {/* Primary CTA — the bridge into System B */}
      <div className="relative overflow-hidden rounded-3xl border border-primary/20 bg-gradient-to-br from-primary/[0.08] to-accent/[0.04] p-6">
        <div className="pointer-events-none absolute -right-10 -top-10 h-32 w-32 rounded-full bg-primary/20 blur-3xl" />
        <div className="relative flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
              <Sparkles className="h-4 w-4 text-primary" />
              Become this
            </h2>
            <p className="mt-1 text-sm text-white/55">
              Generate a personalized learning system that closes every gap for this role.
            </p>
          </div>
          <Button size="lg" onClick={startGeneration} className="shrink-0">
            Generate my path
          </Button>
        </div>
      </div>

      <a
        href={job.redirect_url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 py-3.5 text-sm font-medium text-white/70 transition-colors hover:border-white/25 hover:text-white"
      >
        View original posting
        <ExternalLink className="h-4 w-4" />
      </a>
    </div>
  )
}

export default function JobDetailPage() {
  return (
    <Suspense fallback={<DetailSkeleton />}>
      <JobDetailContent />
    </Suspense>
  )
}
