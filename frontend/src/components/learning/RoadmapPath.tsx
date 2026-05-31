'use client'

import { motion } from 'framer-motion'
import { Flag, MapPin } from 'lucide-react'
import type { Curriculum, SubskillProgress } from '@/lib/types'
import { SkillNode, type NodeStatus } from './SkillNode'
import { skillProgress } from '@/lib/store/journey'
import { staggerContainer } from '@/lib/motion'
import { cn, polishUiSentence } from '@/lib/utils'

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
    <div className="relative mx-auto max-w-4xl">
      {/* center track */}
      <div className="absolute left-6 top-0 h-full w-px bg-gradient-to-b from-white/[0.03] via-white/10 to-white/[0.03] sm:left-1/2 sm:-translate-x-1/2">
        <div className="absolute inset-x-[-12px] inset-y-0 rounded-full bg-[radial-gradient(circle,rgba(178,0,67,0.12),transparent_72%)] opacity-60" />
        <motion.div
          className="relative w-full bg-gradient-to-b from-primary via-primary to-accent shadow-[0_0_22px_rgba(178,0,67,0.45)]"
          initial={{ height: 0 }}
          animate={{ height: `${overall * 100}%` }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </div>

      {/* start marker */}
      <div className="relative mb-8 flex items-center gap-3 pl-14 sm:mb-14 sm:justify-center sm:pl-0">
        <span className="absolute left-6 grid h-6 w-6 -translate-x-1/2 place-items-center rounded-full border border-white/[0.08] bg-[linear-gradient(180deg,rgba(20,24,37,0.95),rgba(10,13,21,0.88))] shadow-[0_12px_30px_-18px_rgba(0,0,0,0.85)] sm:left-1/2">
          <MapPin className="h-3 w-3 text-white/60" />
        </span>
        <span className="text-xs font-medium uppercase tracking-wider text-white/40 sm:relative sm:z-10 sm:-translate-y-6 sm:rounded-full sm:bg-base-950/92 sm:px-3 sm:py-1.5">
          You today
        </span>
      </div>

      {/* stations */}
      <motion.div
        variants={staggerContainer(0.1)}
        initial="hidden"
        animate="show"
        className="space-y-8 sm:space-y-10"
      >
        {curriculum.skills.map((skill, i) => {
          const ratio = ratios[i]
          const status: NodeStatus = ratio >= 1 ? 'complete' : i === activeIdx ? 'active' : 'available'
          return (
            <div
              key={skill.skill_id}
              className="relative pl-14 sm:grid sm:grid-cols-[minmax(0,1fr)_4.75rem_minmax(0,1fr)] sm:items-center sm:pl-0"
            >
              {/* node dot on the track */}
              <span
                className={cn(
                  'absolute left-6 top-9 z-10 h-3.5 w-3.5 -translate-x-1/2 rounded-full border border-white/10 shadow-[0_0_0_5px_rgba(5,7,13,0.98)] sm:left-auto sm:top-1/2 sm:col-start-2 sm:mx-auto sm:-translate-x-0 sm:-translate-y-1/2',
                  status === 'complete'
                    ? 'bg-primary shadow-[0_0_0_5px_rgba(5,7,13,0.98),0_0_18px_rgba(178,0,67,0.42)]'
                    : status === 'active'
                      ? 'bg-[linear-gradient(180deg,#ff7aa6,#b20043)] shadow-[0_0_0_5px_rgba(5,7,13,0.98),0_0_20px_rgba(178,0,67,0.5)]'
                      : 'bg-white/22',
                )}
              />
              <div className={cn(i % 2 === 0 ? 'sm:col-start-1 sm:pr-4 lg:pr-7' : 'sm:col-start-3 sm:pl-4 lg:pl-7')}>
                <SkillNode
                  skill={skill}
                  progress={ratio}
                  status={status}
                  side={i % 2 === 0 ? 'left' : 'right'}
                  index={i}
                />
              </div>
            </div>
          )
        })}
      </motion.div>

      {/* destination marker */}
      <div className="relative mt-14 flex items-center gap-3 pl-14 sm:mt-20 sm:justify-center sm:pl-0">
        <span className="absolute left-6 grid h-7 w-7 -translate-x-1/2 place-items-center rounded-full border border-primary/30 bg-[linear-gradient(180deg,rgba(178,0,67,0.26),rgba(178,0,67,0.08))] shadow-[0_0_20px_rgba(178,0,67,0.28)] sm:left-1/2">
          <Flag className="h-3.5 w-3.5 text-primary" />
        </span>
        <span className="max-w-[18rem] text-left font-display text-sm font-semibold leading-tight text-primary sm:max-w-sm sm:translate-y-7 sm:text-center">
          {polishUiSentence(curriculum.target_role.title)}
        </span>
      </div>
    </div>
  )
}
