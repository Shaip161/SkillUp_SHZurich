'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Check, Loader2 } from 'lucide-react'

const CHECKS = ['Reviewing your explanation', 'Looking for clear reasoning', 'Checking how you would apply it']

/**
 * Step 7.4 — "Agent Validation". A short sequence where AI agents appear to
 * validate the submission before the result is revealed. Calls `onDone` after
 * the checks animate through (the real evaluation runs in parallel).
 */
export function ValidationOverlay({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    if (step >= CHECKS.length) {
      const t = setTimeout(onDone, 350)
      return () => clearTimeout(t)
    }
    const t = setTimeout(() => setStep((s) => s + 1), 600)
    return () => clearTimeout(t)
  }, [step, onDone])

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rounded-2xl border border-white/10 bg-white/[0.03] p-6"
    >
      <p className="mb-4 flex items-center gap-2 text-sm font-medium text-white/70">
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent/60" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
        </span>
        Reviewing your response
      </p>
      <ul className="space-y-2.5">
        {CHECKS.map((label, i) => {
          const complete = i < step
          const active = i === step
          return (
            <li key={label} className="flex items-center gap-2.5 text-sm">
              {complete ? (
                <Check className="h-4 w-4 text-primary" />
              ) : active ? (
                <Loader2 className="h-4 w-4 animate-spin text-accent" />
              ) : (
                <span className="h-4 w-4 rounded-full border border-white/15" />
              )}
              <span className={complete ? 'text-white/70' : active ? 'text-white' : 'text-white/35'}>
                {label}
              </span>
            </li>
          )
        })}
      </ul>
    </motion.div>
  )
}
