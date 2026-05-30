import Image from 'next/image'
import Link from 'next/link'
import { cn } from '@/lib/utils'

/** Brand mark — official Skill Up icon + wordmark. */
export function Logo({ href = '/', className }: { href?: string; className?: string }) {
  return (
    <Link href={href} className={cn('group flex items-center gap-2.5', className)}>
      <span className="relative grid h-10 w-10 place-items-center overflow-hidden rounded-xl bg-gradient-to-br from-primary/30 via-primary/10 to-accent/20 ring-1 ring-white/10">
        <Image
          src="/brand/skill-up-icon-white.svg"
          alt=""
          aria-hidden
          width={28}
          height={24}
          className="h-6 w-auto"
          priority
        />
      </span>
      <span className="flex flex-col leading-none">
        <span className="font-display text-[15px] font-bold tracking-tight text-white">
          Skill <span className="text-accent">Up</span>
        </span>
        <span className="text-[9px] uppercase tracking-[0.18em] text-white/35">
          Career Evolution OS
        </span>
      </span>
    </Link>
  )
}
