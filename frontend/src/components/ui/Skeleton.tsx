import { cn } from '@/lib/utils'

/** Shared shimmer skeleton block. */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('shimmer animate-shimmer rounded-lg', className)}
      {...props}
    />
  )
}
