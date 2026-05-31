'use client'

import { Button } from '@/components/ui/Button'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <p className="font-display text-xl font-semibold text-white">Something went wrong</p>
      <p className="max-w-sm text-sm text-white/50">
        {error.message || 'An unexpected error occurred. Please try again.'}
      </p>
      <Button variant="secondary" onClick={reset}>
        Try again
      </Button>
    </div>
  )
}
