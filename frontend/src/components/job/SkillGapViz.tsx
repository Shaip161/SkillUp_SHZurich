'use client'

import { motion } from 'framer-motion'
import { Check, Plus } from 'lucide-react'
import type { GapResponse } from '@/lib/types'
import { ProgressBar } from '@/components/ui/ProgressBar'

/**
 * Skill-gap visualization for the target-detail screen: how much of the role you
 * already embody vs. what's left to grow into. Framed as trajectory, not deficit.
 */
export function SkillGapViz({ gap }: { gap: GapResponse }) {
  const total = gap.matched_skills.length + gap.missing_skills.length
  const ratio = total === 0 ? 1 : gap.matched_skills.length / total

  return (
    <div className="space-y-5">
      <div className="flex items-end justify-between">
        <div>
          <h2 className="font-display text-lg font-semibold">Your trajectory</h2>
          <p className="mt-0.5 text-sm text-white/45">
            {gap.missing_skills.length === 0
              ? 'You already hold every required skill.'
              : `${gap.matched_skills.length} of ${total} skills in place — ${gap.missing_skills.length} to evolve.`}
          </p>
        </div>
        <span className="font-display text-2xl font-bold text-primary tabular-nums">
          {Math.round(ratio * 100)}%
        </span>
      </div>

      <ProgressBar value={ratio} tone="gradient" />

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border border-primary/20 bg-primary/[0.05] p-4">
          <p className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-primary-200">
            <Check className="h-3.5 w-3.5" /> Already yours
          </p>
          <div className="space-y-1.5">
            {gap.matched_skills.length === 0 && (
              <p className="text-sm text-white/40">No direct matches yet — that's where we begin.</p>
            )}
            {gap.matched_skills.map((s, i) => (
              <motion.div
                key={s}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="text-sm text-white/75"
              >
                {s}
              </motion.div>
            ))}
          </div>
        </div>

        <div className="rounded-2xl border border-amber-400/20 bg-amber-400/[0.04] p-4">
          <p className="mb-3 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-amber-200">
            <Plus className="h-3.5 w-3.5" /> To grow into
          </p>
          <div className="space-y-1.5">
            {gap.missing_skills.length === 0 && (
              <p className="text-sm text-white/40">Nothing missing — you're ready.</p>
            )}
            {gap.missing_skills.map((s, i) => (
              <motion.div
                key={s}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className="text-sm text-white/75"
              >
                {s}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
