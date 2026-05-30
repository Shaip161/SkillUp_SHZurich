'use client'

import { Suspense, useEffect, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft, ExternalLink, MapPin, Tag } from 'lucide-react'
import type { GapResponse, JobDetail } from '@/lib/types'
import { getJob, getSkillGap } from '@/lib/api'
import { SkillBadge } from '@/components/SkillBadge'
import { SkillGap } from '@/components/SkillGap'

function getVariant(
  skill: string,
  gap: GapResponse | null,
): 'matched' | 'missing' | 'neutral' {
  if (!gap) return 'neutral'
  const lower = skill.toLowerCase()
  if (gap.matched_skills.some((m) => m.toLowerCase() === lower)) return 'matched'
  if (gap.missing_skills.some((m) => m.toLowerCase() === lower)) return 'missing'
  return 'neutral'
}

function Skeleton() {
  return (
    <div className="mx-auto max-w-3xl animate-pulse space-y-8">
      <div className="h-4 w-28 rounded bg-white/10" />
      <div className="space-y-3">
        <div className="h-9 w-3/4 rounded-lg bg-white/10" />
        <div className="h-4 w-1/3 rounded bg-white/10" />
      </div>
      <div className="space-y-2">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-4 rounded bg-white/10" style={{ width: `${85 - i * 8}%` }} />
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="h-6 w-20 rounded-full bg-white/10" />
        ))}
      </div>
    </div>
  )
}

function JobDetailContent() {
  const params = useParams()
  const searchParams = useSearchParams()
  const router = useRouter()
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
        setError(err instanceof Error ? err.message : 'Failed to load job details')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [jobId, userId])

  if (loading) return <Skeleton />

  if (error || !job) {
    return (
      <div className="space-y-4 py-16 text-center">
        <p className="text-white/50">{error ?? 'Job not found.'}</p>
        <button
          onClick={() => router.push('/matches')}
          className="text-sm text-teal-400 underline hover:text-teal-300"
        >
          Back to matches
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-3xl space-y-10">

      {/* Back */}
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
          <h1 className="text-3xl font-bold leading-tight text-white">{job.title}</h1>
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
            {job.seniority && job.seniority !== 'unknown' && (
              <span className="capitalize rounded-full bg-white/10 px-2.5 py-0.5 text-xs text-white/60">
                {job.seniority}
              </span>
            )}
          </div>
        </div>

        {/* Apply — desktop, top-right */}
        <a
          href={job.redirect_url}
          target="_blank"
          rel="noopener noreferrer"
          className="hidden shrink-0 items-center gap-2 rounded-xl bg-teal-500 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-teal-400 sm:flex"
        >
          Apply on Adzuna
          <ExternalLink className="h-4 w-4" />
        </a>
      </div>

      {/* Description */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold text-white/80">About the role</h2>
        <p className="whitespace-pre-line text-sm leading-relaxed text-white/60">
          {job.description}
        </p>
      </section>

      {/* Skills */}
      <section className="space-y-5">
        <h2 className="text-base font-semibold text-white/80">Skills</h2>

        {job.required_skills.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-white/30">Required</p>
            <div className="flex flex-wrap gap-1.5">
              {job.required_skills.map((s) => (
                <SkillBadge key={s} skill={s} variant={getVariant(s, gap)} />
              ))}
            </div>
          </div>
        )}

        {job.nice_to_have.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-white/30">Nice to have</p>
            <div className="flex flex-wrap gap-1.5">
              {job.nice_to_have.map((s) => (
                <SkillBadge key={s} skill={s} variant="neutral" />
              ))}
            </div>
          </div>
        )}

        {job.soft_skills.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs uppercase tracking-wider text-white/30">Soft skills</p>
            <div className="flex flex-wrap gap-1.5">
              {job.soft_skills.map((s) => (
                <SkillBadge key={s} skill={s} variant="neutral" />
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Skill gap */}
      {gap && <SkillGap gap={gap} />}

      {/* Apply — full width at bottom */}
      <a
        href={job.redirect_url}
        target="_blank"
        rel="noopener noreferrer"
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-500 py-4 text-base font-semibold text-white transition-colors hover:bg-teal-400"
      >
        Apply on Adzuna
        <ExternalLink className="h-5 w-5" />
      </a>

    </div>
  )
}

export default function JobDetailPage() {
  return (
    <Suspense fallback={<Skeleton />}>
      <JobDetailContent />
    </Suspense>
  )
}
