'use client'

import { motion } from 'framer-motion'
import { cn, clamp } from '@/lib/utils'

interface ProgressBarProps {
  /** 0..1 */
  value: number
  className?: string
  tone?: 'primary' | 'accent' | 'gradient'
  showLabel?: boolean
}

const tones: Record<NonNullable<ProgressBarProps['tone']>, string> = {
  primary: 'bg-primary',
  accent: 'bg-accent',
  gradient: 'bg-gradient-to-r from-primary to-accent',
}

export function ProgressBar({ value, className, tone = 'gradient', showLabel }: ProgressBarProps) {
  const pct = clamp(value) * 100
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
        <motion.div
          className={cn('h-full rounded-full', tones[tone])}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>
      {showLabel && (
        <span className="w-9 text-right text-xs font-semibold tabular-nums text-white/70">
          {Math.round(pct)}%
        </span>
      )}
    </div>
  )
}
