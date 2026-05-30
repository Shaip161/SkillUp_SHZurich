'use client'

import { motion } from 'framer-motion'
import { AlertTriangle, CheckCircle2, RotateCcw } from 'lucide-react'
import type { StageEvaluation } from '@/lib/types'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { Button } from '@/components/ui/Button'

/** Score + verdict card shown after agent validation, with iterate-not-punish framing. */
export function EvaluationResultCard({
  ev,
  onContinue,
  onRetry,
  continueLabel = 'Continue',
}: {
  ev: StageEvaluation
  onContinue: () => void
  onRetry: () => void
  continueLabel?: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-2xl border p-6 ${
        ev.passed ? 'border-primary/30 bg-primary/[0.05]' : 'border-amber-400/25 bg-amber-400/[0.04]'
      }`}
    >
      <div className="flex items-center gap-4">
        <ProgressRing value={ev.score} size={64} stroke={6} tone={ev.passed ? 'primary' : 'accent'} />
        <div>
          <p className="flex items-center gap-2 font-display text-lg font-semibold">
            {ev.passed ? (
              <>
                <CheckCircle2 className="h-5 w-5 text-primary" /> Nicely done
              </>
            ) : (
              <>
                <AlertTriangle className="h-5 w-5 text-amber-300" /> Not quite yet
              </>
            )}
          </p>
          <p className="mt-0.5 text-sm text-white/55">{ev.feedback}</p>
        </div>
      </div>

      {ev.errors.length > 0 && (
        <ul className="mt-4 space-y-1.5 rounded-xl border border-white/8 bg-white/[0.02] p-3">
          {ev.errors.map((e, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-white/60">
              <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-amber-300" />
              {e}
            </li>
          ))}
        </ul>
      )}

      <div className="mt-5 flex gap-3">
        {ev.passed ? (
          <Button onClick={onContinue}>{continueLabel}</Button>
        ) : (
          <Button variant="secondary" onClick={onRetry}>
            <RotateCcw className="h-4 w-4" />
            {ev.stage === 'evaluation' ? 'Review & retry' : 'Try again'}
          </Button>
        )}
      </div>
    </motion.div>
  )
}
