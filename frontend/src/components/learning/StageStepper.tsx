'use client'

import { Check } from 'lucide-react'
import type { StageType } from '@/lib/types'
import { cn } from '@/lib/utils'

const STAGES: { type: StageType; label: string }[] = [
  { type: 'introduction', label: 'Intro' },
  { type: 'conceptual', label: 'Concept' },
  { type: 'practical', label: 'Practice' },
  { type: 'evaluation', label: 'Evaluation' },
]

/** The 5-stage pipeline indicator (reflection shown only during remediation). */
export function StageStepper({
  completed,
  current,
  inRemediation,
}: {
  completed: StageType[]
  current: StageType | null
  inRemediation?: boolean
}) {
  const items = inRemediation ? [...STAGES, { type: 'reflection' as StageType, label: 'Reflect' }] : STAGES

  return (
    <div className="flex items-center">
      {items.map((s, i) => {
        const done = completed.includes(s.type)
        const active = current === s.type
        return (
          <div key={s.type} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <span
                className={cn(
                  'grid h-7 w-7 place-items-center rounded-full text-[11px] font-semibold transition-colors',
                  done
                    ? 'bg-primary text-white'
                    : active
                      ? 'bg-white/10 text-white ring-2 ring-primary'
                      : 'bg-white/5 text-white/35',
                )}
              >
                {done ? <Check className="h-3.5 w-3.5" /> : i + 1}
              </span>
              <span
                className={cn(
                  'text-[10px] font-medium',
                  active ? 'text-white' : done ? 'text-primary-200' : 'text-white/35',
                )}
              >
                {s.label}
              </span>
            </div>
            {i < items.length - 1 && (
              <div className="mx-1 h-px flex-1 bg-white/10">
                <div className={cn('h-full', done ? 'bg-primary' : 'bg-transparent')} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
