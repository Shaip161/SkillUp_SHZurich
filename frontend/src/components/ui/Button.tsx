'use client'

import { forwardRef } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

const button = cva(
  'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/60 disabled:pointer-events-none disabled:opacity-40 active:scale-[0.98]',
  {
    variants: {
      variant: {
        primary:
          'border border-primary/25 bg-[linear-gradient(135deg,rgba(205,22,93,0.96),rgba(178,0,67,0.98)_42%,rgba(123,0,47,0.98))] text-white shadow-[0_18px_44px_-18px_rgba(178,0,67,0.72),inset_0_1px_0_rgba(255,255,255,0.1)] hover:brightness-[1.05] hover:shadow-[0_22px_52px_-18px_rgba(178,0,67,0.82),0_0_28px_-12px_rgba(178,0,67,0.55)]',
        accent:
          'border border-accent/20 bg-[linear-gradient(135deg,rgba(255,154,68,0.98),rgba(255,112,0,0.98)_40%,rgba(214,92,0,0.98))] text-base-950 shadow-[0_18px_42px_-18px_rgba(255,112,0,0.6),inset_0_1px_0_rgba(255,255,255,0.12)] hover:brightness-[1.04] hover:shadow-[0_22px_48px_-18px_rgba(255,112,0,0.75)]',
        secondary:
          'border border-white/[0.08] bg-[linear-gradient(180deg,rgba(21,25,38,0.94),rgba(11,14,24,0.82))] text-white shadow-[0_20px_40px_-28px_rgba(0,0,0,0.72),inset_0_1px_0_rgba(255,255,255,0.05)] hover:border-white/[0.14] hover:bg-[linear-gradient(180deg,rgba(26,31,46,0.96),rgba(13,17,29,0.84))]',
        outline:
          'border border-white/[0.12] bg-white/[0.015] text-white hover:border-white/[0.2] hover:bg-white/[0.05]',
        ghost: 'text-white/70 hover:text-white hover:bg-white/[0.05]',
      },
      size: {
        sm: 'h-9 px-3.5 text-sm',
        md: 'h-11 px-5 text-sm',
        lg: 'h-12 px-7 text-base',
      },
    },
    defaultVariants: { variant: 'primary', size: 'md' },
  },
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
  VariantProps<typeof button> {
  loading?: boolean
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, children, disabled, ...props }, ref) => (
    <button
      ref={ref}
      className={cn(button({ variant, size }), className)}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  ),
)
Button.displayName = 'Button'
