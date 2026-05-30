'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Check, Lock, Play } from 'lucide-react'
import type { CurriculumSkill } from '@/lib/types'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { fadeUp } from '@/lib/motion'
import { cn } from '@/lib/utils'

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
        'group relative flex w-full items-center gap-4 rounded-2xl border p-4 text-left transition-all sm:w-[calc(50%-2rem)]',
        side === 'right' ? 'sm:ml-auto' : '',
        status === 'complete'
          ? 'border-primary/30 bg-primary/[0.06]'
          : status === 'active'
            ? 'border-white/15 bg-white/[0.05] hover:border-primary/40 hover:bg-white/[0.07]'
            : 'border-white/10 bg-white/[0.03] hover:border-white/20',
      )}
    >
      {ring}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-white/35">
            Skill {index + 1}
          </span>
          <span className="rounded-full bg-white/5 px-1.5 py-0.5 text-[10px] capitalize text-white/40">
            {skill.difficulty_level}
          </span>
        </div>
        <h3 className="mt-0.5 truncate font-display text-base font-semibold text-white">
          {skill.skill_name}
        </h3>
        <p className="mt-0.5 flex items-center gap-1.5 text-xs text-white/45">
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
