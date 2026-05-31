import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <p className="font-display text-7xl font-bold text-white/10">404</p>
      <p className="text-white/50">This page doesn&apos;t exist.</p>
      <Link
        href="/"
        className="text-sm text-primary underline transition-colors hover:text-primary-300"
      >
        Back to home
      </Link>
    </div>
  )
}
