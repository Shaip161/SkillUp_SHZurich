import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const card = cva('rounded-2xl transition-all duration-300', {
  variants: {
    variant: {
      surface: 'border border-white/10 bg-white/[0.04]',
      glass: 'glass',
      gradient:
        'relative border border-white/10 bg-gradient-to-b from-white/[0.07] to-white/[0.02]',
      ghost: 'border border-transparent',
    },
    interactive: {
      true: 'cursor-pointer hover:border-white/20 hover:bg-white/[0.07] active:scale-[0.995]',
      false: '',
    },
    padded: { true: 'p-6', false: '' },
  },
  defaultVariants: { variant: 'surface', interactive: false, padded: true },
})

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof card> {}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, interactive, padded, ...props }, ref) => (
    <div ref={ref} className={cn(card({ variant, interactive, padded }), className)} {...props} />
  ),
)
Card.displayName = 'Card'

/** Convenience preset: frosted glass card. */
export const GlassCard = forwardRef<HTMLDivElement, Omit<CardProps, 'variant'>>(
  (props, ref) => <Card ref={ref} variant="glass" {...props} />,
)
GlassCard.displayName = 'GlassCard'
