import { cn } from '@/lib/utils'

interface SkillBadgeProps {
  skill: string
  variant: 'matched' | 'missing' | 'neutral'
  className?: string
}

const styles: Record<SkillBadgeProps['variant'], string> = {
  matched: 'bg-teal-500/20 text-teal-300 border-teal-500/30',
  missing: 'bg-red-500/20 text-red-300 border-red-500/30',
  neutral: 'bg-white/10 text-white/50 border-white/10',
}

export function SkillBadge({ skill, variant, className }: SkillBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium',
        styles[variant],
        className,
      )}
    >
      {skill}
    </span>
  )
}
