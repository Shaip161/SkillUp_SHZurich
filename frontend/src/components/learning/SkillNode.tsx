'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Check, Lock, Play } from 'lucide-react'
import type { CurriculumSkill } from '@/lib/types'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { fadeUp } from '@/lib/motion'
import { cn, polishGeneratedLabel } from '@/lib/utils'

export type NodeStatus = 'complete' | 'active' | 'available'

/** A single "station" on the roadmap path. */
export function SkillNode({
  skill,
  progress,
  status,
  side,
  index,
}: {
  skill: CurriculumSkill
  progress: number
  status: NodeStatus
  side: 'left' | 'right'
  index: number
}) {
  const router = useRouter()

  const ring =
    status === 'complete' ? (
      <span className="grid h-14 w-14 place-items-center rounded-full bg-primary/20 ring-2 ring-primary">
        <Check className="h-6 w-6 text-primary" />
      </span>
    ) : (
      <ProgressRing value={progress} size={56} stroke={5} tone={status === 'active' ? 'primary' : 'accent'} label={<span className="text-[11px] font-bold tabular-nums">{Math.round(progress * 100)}%</span>} />
    )

  return (
    <motion.button
      variants={fadeUp}
      onClick={() => router.push(`/roadmap/${skill.skill_id}`)}
      className={cn(
        'group relative flex w-full items-center gap-4 overflow-hidden rounded-[28px] border p-4 text-left transition-all duration-300',
        status === 'complete'
          ? 'border-primary/18 bg-[linear-gradient(180deg,rgba(178,0,67,0.14),rgba(15,19,31,0.92))] shadow-[0_28px_70px_-44px_rgba(178,0,67,0.5),inset_0_1px_0_rgba(255,255,255,0.05)]'
          : status === 'active'
            ? 'border-primary/22 bg-[linear-gradient(180deg,rgba(23,28,44,0.96),rgba(11,15,25,0.88))] shadow-[0_32px_80px_-46px_rgba(178,0,67,0.6),0_0_28px_-16px_rgba(178,0,67,0.35),inset_0_1px_0_rgba(255,255,255,0.06)] hover:-translate-y-0.5 hover:border-primary/32'
            : 'border-white/[0.07] bg-[linear-gradient(180deg,rgba(18,22,35,0.94),rgba(10,13,22,0.82))] shadow-[0_26px_60px_-46px_rgba(0,0,0,0.84),inset_0_1px_0_rgba(255,255,255,0.04)] hover:-translate-y-0.5 hover:border-white/[0.12]',
      )}
    >
      <span
        className={cn(
          'pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100',
          side === 'right'
            ? 'bg-[radial-gradient(circle_at_left_center,rgba(255,255,255,0.04),transparent_44%)]'
            : 'bg-[radial-gradient(circle_at_right_center,rgba(255,255,255,0.04),transparent_44%)]',
        )}
      />
      {ring}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-white/35">
            Skill {index + 1}
          </span>
          <span className="rounded-full border border-white/8 bg-white/[0.04] px-1.5 py-0.5 text-[10px] capitalize text-white/46">
            {skill.difficulty_level}
          </span>
        </div>
        <h3 className="mt-1 font-display text-base font-semibold leading-6 text-white">
          {polishGeneratedLabel(skill.skill_name)}
        </h3>
        <p className="mt-1.5 flex items-center gap-1.5 text-xs text-white/48">
          {status === 'complete' ? (
            'Mastered'
          ) : status === 'active' ? (
            <>
              <Play className="h-3 w-3 text-primary" /> Continue
            </>
          ) : (
            <>
              <Lock className="h-3 w-3" /> {skill.subskills.length} subskills
            </>
          )}
        </p>
      </div>
    </motion.button>
  )
}
