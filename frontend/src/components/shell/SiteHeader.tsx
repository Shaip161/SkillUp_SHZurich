'use client'

import { Logo } from '@/components/ui/Logo'

/** One adaptive header for the whole platform — marketing vs in-app. */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/[0.06] bg-base-950/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center px-4 sm:px-6">
        <Logo />
      </div>
    </header>
  )
}
