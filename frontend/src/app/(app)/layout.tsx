'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Loader2 } from 'lucide-react'
import { PageTransition } from '@/components/ui/motion'
import { useSession } from '@/lib/store/session'

/**
 * Shell + auth gate for the authenticated journey (System A matches + System B
 * learning). Route groups don't affect URLs, so /matches and /jobs/[id] keep
 * their paths. Redirects to /login when there's no (mock) session.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { session, ready } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (ready && !session) router.replace('/login')
  }, [ready, session, router])

  if (!ready || !session) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    )
  }

  return <PageTransition>{children}</PageTransition>
}
