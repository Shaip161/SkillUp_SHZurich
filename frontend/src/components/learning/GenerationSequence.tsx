'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { drawLine } from '@/lib/motion'

const PHASES = [
  'Analyzing your skill gaps…',
  'Mapping transferable strengths…',
  'Composing your skill graph…',
  'Building the adaptive roadmap…',
  'Optimizing your progression path…',
]

// A fixed node layout for the "AI building a skill graph" visual.
const NODES: { x: number; y: number; r?: number; core?: boolean }[] = [
  { x: 50, y: 50, r: 9, core: true },
  { x: 18, y: 26 },
  { x: 82, y: 24 },
  { x: 14, y: 72 },
  { x: 86, y: 74 },
  { x: 50, y: 14 },
  { x: 30, y: 88 },
  { x: 72, y: 90 },
]
const EDGES = [
  [0, 1],
  [0, 2],
  [0, 3],
  [0, 4],
  [0, 5],
  [1, 5],
  [2, 5],
  [3, 6],
  [4, 7],
]

/**
 * Step 4 — cinematic "an AI is generating your evolution path" sequence.
 * Cycles phase copy while an SVG skill-graph assembles. Calls `onComplete`
 * once both the minimum dramatic duration has elapsed AND `ready` is true.
 */
export function GenerationSequence({
  ready,
  onComplete,
  targetTitle,
}: {
  ready: boolean
  onComplete: () => void
  targetTitle: string
}) {
  const [phase, setPhase] = useState(0)
  const [minElapsed, setMinElapsed] = useState(false)

  useEffect(() => {
    const id = setInterval(() => setPhase((p) => Math.min(p + 1, PHASES.length - 1)), 700)
    const min = setTimeout(() => setMinElapsed(true), 2800)
    return () => {
      clearInterval(id)
      clearTimeout(min)
    }
  }, [])

  useEffect(() => {
    if (ready && minElapsed) {
      const t = setTimeout(onComplete, 500)
      return () => clearTimeout(t)
    }
  }, [ready, minElapsed, onComplete])

  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center text-center">
      <div className="relative h-64 w-64">
        {/* rotating ambient ring */}
        <div className="absolute inset-0 animate-spin-slow rounded-full border border-primary/15" />
        <div className="absolute inset-6 animate-pulse-glow rounded-full bg-primary/[0.06] blur-2xl" />

        <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full">
          {EDGES.map(([a, b], i) => (
            <motion.line
              key={`e${i}`}
              x1={NODES[a].x}
              y1={NODES[a].y}
              x2={NODES[b].x}
              y2={NODES[b].y}
              stroke="rgba(52,224,161,0.45)"
              strokeWidth="0.5"
              variants={drawLine}
              initial="hidden"
              animate="show"
              transition={{ delay: 0.3 + i * 0.12 }}
            />
          ))}
          {NODES.map((n, i) => (
            <motion.circle
              key={`n${i}`}
              cx={n.x}
              cy={n.y}
              r={n.r ?? 3.2}
              fill={n.core ? '#34e0a1' : '#38bdf8'}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: i * 0.14, type: 'spring', stiffness: 260, damping: 18 }}
              style={{ filter: `drop-shadow(0 0 4px ${n.core ? '#34e0a1' : '#38bdf8'})`, transformOrigin: `${n.x}px ${n.y}px` }}
            />
          ))}
        </svg>
      </div>

      <motion.p
        key={phase}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-10 font-display text-xl font-medium text-white"
      >
        {PHASES[phase]}
      </motion.p>
      <p className="mt-2 text-sm text-white/40">
        Designing your path to <span className="text-primary">{targetTitle}</span>
      </p>

      {/* progress dots */}
      <div className="mt-6 flex gap-1.5">
        {PHASES.map((_, i) => (
          <span
            key={i}
            className={`h-1.5 w-1.5 rounded-full transition-colors ${i <= phase ? 'bg-primary' : 'bg-white/15'}`}
          />
        ))}
      </div>
    </div>
  )
}
