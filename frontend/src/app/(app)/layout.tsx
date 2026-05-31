'use client'

import { PageTransition } from '@/components/ui/motion'

/**
 * Shell for the app journey (System A matches + System B
 * learning). Route groups don't affect URLs, so /matches and /jobs/[id] keep
 * their paths.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <PageTransition>{children}</PageTransition>
}
