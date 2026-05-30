'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowUpRight, MapPin, Sparkles } from 'lucide-react'
import type { JobMatchResult } from '@/lib/types'
import { Badge } from '@/components/ui/Badge'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { fadeUp } from '@/lib/motion'
import { cn } from '@/lib/utils'

/**
 * Step 3 — an aspirational "future self" card. The user isn't picking a course;
 * they're choosing a future version of themselves. Compatibility ring, a glimpse
 * of what they already bring, and what's left to grow into.
 */
export function TargetJobCard({
  match,
  userId,
  index = 0,
}: {
  match: JobMatchResult
  userId: string
  index?: number
}) {
  const router = useRouter()
  const { job, score, matched_skills, missing_skills } = match
  const open = () => router.push(`/jobs/${job.id}?user_id=${userId}`)

  return (
    <motion.div
      variants={fadeUp}
      role="button"
      tabIndex={0}
      onClick={open}
      onKeyDown={(e) => e.key === 'Enter' && open()}
      className={cn(
        'group relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-b from-white/[0.06] to-white/[0.02] p-6 transition-all duration-300',
        'hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-[0_24px_60px_-24px_rgba(52,224,161,0.4)]',
      )}
    >
      {/* glow accent */}
      <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-primary/10 blur-3xl transition-opacity duration-300 group-hover:opacity-100 opacity-50" />

      <div className="relative flex items-start justify-between gap-4">
        <div className="min-w-0">
          {index === 0 && (
            <span className="mb-2 inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-primary-200">
              <Sparkles className="h-3 w-3" /> Best fit
            </span>
          )}
          <h3 className="font-display text-xl font-semibold leading-tight text-white">{job.title}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-white/45">
            {job.company && <span className="truncate">{job.company}</span>}
            {job.location && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {job.location}
              </span>
            )}
            {job.seniority && job.seniority !== 'unknown' && (
              <span className="capitalize">{job.seniority}</span>
            )}
          </div>
        </div>
        <ProgressRing value={score} size={56} stroke={5} tone="primary" />
      </div>

      {/* Skill snapshot */}
      <div className="relative mt-5 space-y-2.5">
        {matched_skills.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {matched_skills.slice(0, 4).map((s) => (
              <Badge key={s} variant="matched">
                {s}
              </Badge>
            ))}
          </div>
        )}
        {missing_skills.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {missing_skills.slice(0, 3).map((s) => (
              <Badge key={s} variant="missing">
                {s}
              </Badge>
            ))}
            {missing_skills.length > 3 && (
              <span className="text-xs text-white/35">+{missing_skills.length - 3} to grow</span>
            )}
          </div>
        )}
      </div>

      <div className="relative mt-5 flex items-center justify-between border-t border-white/[0.06] pt-4">
        <span className="text-xs text-white/40">
          {missing_skills.length === 0
            ? 'You already qualify'
            : `${missing_skills.length} skill${missing_skills.length === 1 ? '' : 's'} between you and this role`}
        </span>
        <span className="flex items-center gap-1 text-sm font-medium text-primary transition-transform group-hover:translate-x-0.5">
          Explore
          <ArrowUpRight className="h-4 w-4" />
        </span>
      </div>
    </motion.div>
  )
}
