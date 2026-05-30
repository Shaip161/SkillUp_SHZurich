'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { LogOut, Map } from 'lucide-react'
import { Logo } from '@/components/ui/Logo'
import { Button } from '@/components/ui/Button'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { useSession } from '@/lib/store/session'
import { useJourney, overallProgress } from '@/lib/store/journey'
import { initials, cn } from '@/lib/utils'

/** One adaptive header for the whole platform — marketing vs in-app. */
export function SiteHeader() {
  const pathname = usePathname()
  const router = useRouter()
  const { session, signOut } = useSession()
  const { state, reset } = useJourney()

  const inApp =
    pathname?.startsWith('/roadmap') ||
    pathname?.startsWith('/matches') ||
    pathname?.startsWith('/jobs') ||
    pathname?.startsWith('/upload') ||
    pathname?.startsWith('/generate')

  const overall = overallProgress(state.curriculum, state.progress)

  function handleSignOut() {
    reset()
    signOut()
    router.push('/')
  }

  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-base-950/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center justify-between px-4 sm:px-6">
        <Logo />

        <div className="flex items-center gap-3">
          {inApp && state.curriculum && (
            <Link
              href="/roadmap"
              className={cn(
                'hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:border-white/20 hover:text-white sm:flex',
              )}
            >
              <Map className="h-3.5 w-3.5 text-primary" />
              Roadmap
              <span className="tabular-nums text-white/40">{Math.round(overall * 100)}%</span>
            </Link>
          )}

          {inApp && state.curriculum && (
            <ProgressRing value={overall} size={36} stroke={4} className="sm:hidden" label={<span className="text-[9px] font-bold">{Math.round(overall * 100)}</span>} />
          )}

          {session ? (
            <div className="flex items-center gap-2">
              <span className="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-primary/30 to-accent/20 text-xs font-semibold ring-1 ring-white/10">
                {initials(session.email)}
              </span>
              <button
                onClick={handleSignOut}
                aria-label="Sign out"
                className="grid h-9 w-9 place-items-center rounded-full text-white/40 transition-colors hover:bg-white/5 hover:text-white"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          ) : (
            pathname !== '/login' && (
              <Button size="sm" variant="secondary" onClick={() => router.push('/login')}>
                Sign in
              </Button>
            )
          )}
        </div>
      </div>
    </header>
  )
}
