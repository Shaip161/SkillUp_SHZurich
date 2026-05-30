import Link from 'next/link'
import { cn } from '@/lib/utils'

/** Brand mark — an abstract "evolution node" glyph + wordmark. */
export function Logo({ href = '/', className }: { href?: string; className?: string }) {
  return (
    <Link href={href} className={cn('group flex items-center gap-2.5', className)}>
      <span className="relative grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary/30 to-accent/20 ring-1 ring-white/10">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" aria-hidden>
          <path d="M5 19 L12 5 L19 19" stroke="#34e0a1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="12" cy="5" r="2.4" fill="#38bdf8" />
        </svg>
      </span>
      <span className="flex flex-col leading-none">
        <span className="font-display text-[15px] font-bold tracking-tight">
          Ascend<span className="text-primary">AI</span>
        </span>
        <span className="text-[9px] uppercase tracking-[0.18em] text-white/35">
          Career Evolution OS
        </span>
      </span>
    </Link>
  )
}
