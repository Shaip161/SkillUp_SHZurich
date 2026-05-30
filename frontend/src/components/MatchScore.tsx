import { cn } from '@/lib/utils'

interface MatchScoreProps {
  score: number
  className?: string
}

function scoreColor(pct: number) {
  if (pct >= 75) return { bar: 'bg-teal-400', text: 'text-teal-400' }
  if (pct >= 50) return { bar: 'bg-amber-400', text: 'text-amber-400' }
  return { bar: 'bg-red-400', text: 'text-red-400' }
}

export function MatchScore({ score, className }: MatchScoreProps) {
  const pct = Math.round(score * 100)
  const { bar, text } = scoreColor(pct)

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
        <div
          className={cn('h-full rounded-full transition-all duration-300', bar)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={cn('w-9 text-right text-xs font-semibold tabular-nums', text)}>
        {pct}%
      </span>
    </div>
  )
}
