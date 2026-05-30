'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, Mail } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { useSession } from '@/lib/store/session'

/** Step 1 — minimal, premium mock auth. No backend; creates a local session. */
export default function LoginPage() {
  const router = useRouter()
  const { signIn } = useSession()
  const [email, setEmail] = useState('')
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)

  function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!valid) return
    signIn(email)
    router.push('/upload')
  }

  return (
    <div className="flex min-h-[70vh] items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md"
      >
        <div className="text-center">
          <h1 className="font-display text-3xl font-bold tracking-tight">Welcome back</h1>
          <p className="mt-2 text-sm text-white/50">
            Sign in to continue your evolution. No password is needed for this demo.
          </p>
        </div>

        <form onSubmit={submit} className="glass mt-8 space-y-4 rounded-2xl p-6">
          <label className="block">
            <span className="mb-1.5 block text-xs font-medium uppercase tracking-wider text-white/40">
              Email
            </span>
            <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-3 focus-within:border-primary/50">
              <Mail className="h-4 w-4 text-white/30" />
              <input
                type="email"
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="h-11 flex-1 bg-transparent text-sm text-white placeholder:text-white/25 focus:outline-none"
              />
            </div>
          </label>

          <Button type="submit" size="lg" disabled={!valid} className="w-full">
            Continue
            <ArrowRight className="h-4 w-4" />
          </Button>

          <p className="text-center text-xs text-white/30">
            By continuing you agree this is a demo experience.
          </p>
        </form>
      </motion.div>
    </div>
  )
}
