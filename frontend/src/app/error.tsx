'use client'

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function Error({ error, reset }: ErrorProps) {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <p className="text-lg font-semibold text-white">Something went wrong</p>
      <p className="max-w-sm text-sm text-white/50">
        {error.message || 'An unexpected error occurred. Please try again.'}
      </p>
      <button
        onClick={reset}
        className="rounded-xl bg-white/10 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-white/20"
      >
        Try again
      </button>
    </div>
  )
}
