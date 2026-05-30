'use client'

import { createContext, useCallback, useContext, useEffect, useState } from 'react'

/**
 * Mock/local auth. No backend — a "session" is just a remembered identity in
 * localStorage. Swap `signIn` for a real auth call later; the rest of the app
 * only depends on `{ session, signIn, signOut }`.
 */
export interface Session {
  email: string
  name: string
  /** Reuses System A's user_id concept; null until a CV is matched. */
  userId: string | null
}

interface SessionContextValue {
  session: Session | null
  ready: boolean
  signIn: (email: string) => void
  signOut: () => void
  setUserId: (userId: string) => void
}

const KEY = 'ascend.session'
const SessionContext = createContext<SessionContextValue | null>(null)

function deriveName(email: string): string {
  const handle = email.split('@')[0].replace(/[._-]+/g, ' ').trim()
  return handle.replace(/\b\w/g, (c) => c.toUpperCase()) || 'Explorer'
}

export function SessionProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [ready, setReady] = useState(false)

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY)
      if (raw) setSession(JSON.parse(raw) as Session)
    } catch {
      /* ignore corrupt storage */
    }
    setReady(true)
  }, [])

  const persist = useCallback((next: Session | null) => {
    setSession(next)
    try {
      if (next) localStorage.setItem(KEY, JSON.stringify(next))
      else localStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
  }, [])

  const signIn = useCallback(
    (email: string) => persist({ email, name: deriveName(email), userId: null }),
    [persist],
  )
  const signOut = useCallback(() => persist(null), [persist])
  const setUserId = useCallback(
    (userId: string) => persist(session ? { ...session, userId } : session),
    [persist, session],
  )

  return (
    <SessionContext.Provider value={{ session, ready, signIn, signOut, setUserId }}>
      {children}
    </SessionContext.Provider>
  )
}

export function useSession(): SessionContextValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession must be used within <SessionProvider>')
  return ctx
}
