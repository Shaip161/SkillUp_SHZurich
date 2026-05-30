'use client'

import { useRouter } from 'next/navigation'
import { ChevronRight, MapPin, Tag } from 'lucide-react'
import type { JobMatchResult } from '@/lib/types'
import { cn } from '@/lib/utils'
import { MatchScore } from './MatchScore'
import { SkillBadge } from './SkillBadge'

interface JobCardProps {
  match: JobMatchResult
  userId: string
  className?: string
}

export function JobCard({ match, userId, className }: JobCardProps) {
  const router = useRouter()
  const { job, score, matched_skills, missing_skills } = match

  const visibleMatched = matched_skills.slice(0, 5)
  const visibleMissing = missing_skills.slice(0, 4)
  const extraMissing = missing_skills.length - visibleMissing.length

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => router.push(`/jobs/${job.id}?user_id=${userId}`)}
      onKeyDown={(e) => e.key === 'Enter' && router.push(`/jobs/${job.id}?user_id=${userId}`)}
      className={cn(
        'group cursor-pointer space-y-4 rounded-2xl border border-white/10 bg-white/5 p-5 transition-all',
        'hover:border-white/20 hover:bg-white/[0.08] active:scale-[0.99]',
        className,
      )}
    >
      {/* Title + chevron */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate font-semibold leading-snug text-white">{job.title}</h3>
          {job.company && (
            <p className="mt-0.5 truncate text-sm text-white/50">{job.company}</p>
          )}
        </div>
        <ChevronRight className="mt-0.5 h-4 w-4 shrink-0 text-white/30 transition-transform group-hover:translate-x-0.5" />
      </div>

      {/* Meta */}
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-white/40">
        {job.location && (
          <span className="flex items-center gap-1">
            <MapPin className="h-3 w-3" />
            {job.location}
          </span>
        )}
        {job.category && (
          <span className="flex items-center gap-1">
            <Tag className="h-3 w-3" />
            {job.category}
          </span>
        )}
        {job.seniority && job.seniority !== 'unknown' && (
          <span className="capitalize">{job.seniority}</span>
        )}
      </div>

      {/* Score */}
      <MatchScore score={score} />

      {/* Skills */}
      {(visibleMatched.length > 0 || visibleMissing.length > 0) && (
        <div className="space-y-1.5">
          {visibleMatched.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {visibleMatched.map((s) => (
                <SkillBadge key={s} skill={s} variant="matched" />
              ))}
            </div>
          )}
          {visibleMissing.length > 0 && (
            <div className="flex flex-wrap items-center gap-1">
              {visibleMissing.map((s) => (
                <SkillBadge key={s} skill={s} variant="missing" />
              ))}
              {extraMissing > 0 && (
                <span className="text-xs text-white/30">+{extraMissing} missing</span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
