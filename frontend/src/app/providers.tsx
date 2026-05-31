'use client'

import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SessionProvider } from '@/lib/store/session'
import { JourneyProvider } from '@/lib/store/journey'

/** App-wide client providers: server cache + mock session + journey state. */
export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1, refetchOnWindowFocus: false },
        },
      }),
  )

  return (
    <QueryClientProvider client={client}>
      <SessionProvider>
        <JourneyProvider>{children}</JourneyProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}
