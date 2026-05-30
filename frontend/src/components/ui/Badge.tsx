import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const badge = cva(
  'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium',
  {
    variants: {
      variant: {
        matched: 'border-primary/30 bg-primary/15 text-primary-200',
        missing: 'border-amber-400/30 bg-amber-400/10 text-amber-200',
        neutral: 'border-white/10 bg-white/[0.06] text-white/55',
        accent: 'border-accent/30 bg-accent/15 text-accent-300',
      },
    },
    defaultVariants: { variant: 'neutral' },
  },
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badge> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badge({ variant }), className)} {...props} />
}
