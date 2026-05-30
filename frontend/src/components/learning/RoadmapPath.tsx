'use client'

import { motion } from 'framer-motion'
import { Flag, MapPin } from 'lucide-react'
import type { Curriculum, SubskillProgress } from '@/lib/types'
import { SkillNode, type NodeStatus } from './SkillNode'
import { skillProgress } from '@/lib/store/journey'
import { staggerContainer } from '@/lib/motion'

/**
 * Step 5 — the journey map. A central progress track with skill "stations"
 * alternating sides (timeline style on desktop, stacked on mobile). Reads top
 * (you, today) to bottom (the target role).
 */
export function RoadmapPath({
  curriculum,
  progress,
  overall,
}: {
  curriculum: Curriculum
  progress: Record<string, SubskillProgress>
  overall: number
}) {
  // First not-complete skill becomes the "active" focus.
  const ratios = curriculum.skills.map((s) => skillProgress(s, progress))
  const activeIdx = ratios.findIndex((r) => r < 1)

  return (
    <div className="relative mx-auto max-w-3xl">
      {/* center track */}
      <div className="absolute left-6 top-0 h-full w-px bg-white/10 sm:left-1/2 sm:-translate-x-1/2">
        <motion.div
          className="w-full bg-gradient-to-b from-primary to-accent"
          initial={{ height: 0 }}
          animate={{ height: `${overall * 100}%` }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>

      {/* start marker */}
      <div className="relative mb-8 flex items-center gap-3 pl-14 sm:justify-center sm:pl-0">
        <span className="absolute left-6 grid h-6 w-6 -translate-x-1/2 place-items-center rounded-full bg-base-800 ring-2 ring-white/20 sm:left-1/2">
          <MapPin className="h-3 w-3 text-white/60" />
        </span>
        <span className="text-xs font-medium uppercase tracking-wider text-white/40">You, today</span>
      </div>

      {/* stations */}
      <motion.div
        variants={staggerContainer(0.1)}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        {curriculum.skills.map((skill, i) => {
          const ratio = ratios[i]
          const status: NodeStatus = ratio >= 1 ? 'complete' : i === activeIdx ? 'active' : 'available'
          return (
            <div key={skill.skill_id} className="relative pl-14 sm:pl-0">
              {/* node dot on the track */}
              <span
                className={`absolute left-6 top-7 z-10 h-3 w-3 -translate-x-1/2 rounded-full ring-4 ring-base-950 sm:left-1/2 ${
                  status === 'available' ? 'bg-white/25' : 'bg-primary'
                }`}
              />
              <SkillNode
                skill={skill}
                progress={ratio}
                status={status}
                side={i % 2 === 0 ? 'left' : 'right'}
                index={i}
              />
            </div>
          )
        })}
      </motion.div>

      {/* destination marker */}
      <div className="relative mt-8 flex items-center gap-3 pl-14 sm:justify-center sm:pl-0">
        <span className="absolute left-6 grid h-7 w-7 -translate-x-1/2 place-items-center rounded-full bg-primary/20 ring-2 ring-primary sm:left-1/2">
          <Flag className="h-3.5 w-3.5 text-primary" />
        </span>
        <span className="font-display text-sm font-semibold text-primary">
          {curriculum.target_role.title}
        </span>
      </div>
    </div>
  )
}
