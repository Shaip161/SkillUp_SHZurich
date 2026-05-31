import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const card = cva('rounded-2xl transition-all duration-300', {
  variants: {
    variant: {
      surface:
        'border border-white/[0.06] bg-[linear-gradient(180deg,rgba(17,21,34,0.94),rgba(10,13,22,0.8))] shadow-[0_28px_80px_-52px_rgba(0,0,0,0.88),inset_0_1px_0_rgba(255,255,255,0.04)]',
      glass: 'glass',
      gradient:
        'relative border border-white/[0.07] bg-[linear-gradient(180deg,rgba(22,27,42,0.96),rgba(11,14,24,0.84))] shadow-[0_30px_90px_-56px_rgba(0,0,0,0.9),inset_0_1px_0_rgba(255,255,255,0.05)]',
      ghost: 'border border-transparent',
    },
    interactive: {
      true:
        'cursor-pointer hover:-translate-y-0.5 hover:border-white/[0.12] hover:shadow-[0_34px_90px_-50px_rgba(0,0,0,0.84),inset_0_1px_0_rgba(255,255,255,0.06)] active:scale-[0.995]',
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
