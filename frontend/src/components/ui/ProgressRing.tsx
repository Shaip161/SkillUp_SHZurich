'use client'

import { motion } from 'framer-motion'
import { cn, clamp } from '@/lib/utils'

interface ProgressRingProps {
  /** 0..1 */
  value: number
  size?: number
  stroke?: number
  className?: string
  label?: React.ReactNode
  tone?: 'primary' | 'accent'
}

export function ProgressRing({
  value,
  size = 64,
  stroke = 6,
  className,
  label,
  tone = 'primary',
}: ProgressRingProps) {
  const v = clamp(value)
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const color = tone === 'primary' ? '#34e0a1' : '#38bdf8'

  return (
    <div className={cn('relative inline-flex items-center justify-center', className)} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={stroke} />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - v) }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
          style={{ filter: `drop-shadow(0 0 6px ${color}66)` }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        {label ?? (
          <span className="text-sm font-bold tabular-nums">{Math.round(v * 100)}%</span>
        )}
      </div>
    </div>
  )
}
