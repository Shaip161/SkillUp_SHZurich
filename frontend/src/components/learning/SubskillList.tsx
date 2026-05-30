'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Check, Lock } from 'lucide-react'
import type { CurriculumSkill, SubskillProgress } from '@/lib/types'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { staggerContainer, fadeUp } from '@/lib/motion'
import { isSubskillUnlocked } from '@/lib/store/journey'
import { cn, polishGeneratedLabel } from '@/lib/utils'

const STATUS_LABEL: Record<string, string> = {
  not_started: 'Locked',
  in_progress: 'In progress',
  needs_remediation: 'Needs remediation',
  retry_ready: 'Ready to retry',
  completed: 'Mastered',
}

/** Step 6 — subskills as a layered, sequential progression of milestones. */
export function SubskillList({
  skill,
  progress,
}: {
  skill: CurriculumSkill
  progress: Record<string, SubskillProgress>
}) {
  const router = useRouter()

  return (
    <motion.ol
      variants={staggerContainer(0.08)}
      initial="hidden"
      animate="show"
      className="relative space-y-3"
    >
      {skill.subskills.map((sub, i) => {
        const p = progress[sub.subskill_id]
        const status = p?.mastery_status ?? 'not_started'
        const unlocked = isSubskillUnlocked(skill, sub.subskill_id, progress)
        const complete = status === 'completed'
        const ratio = complete ? 1 : (p?.progress_percent ?? 0) / 100

        return (
          <motion.li key={sub.subskill_id} variants={fadeUp}>
            <button
              disabled={!unlocked}
              onClick={() => router.push(`/roadmap/${skill.skill_id}/${sub.subskill_id}`)}
              className={cn(
                'group flex w-full items-center gap-4 rounded-[24px] border p-4 text-left transition-all duration-300',
                complete
                  ? 'border-primary/20 bg-[linear-gradient(180deg,rgba(178,0,67,0.12),rgba(14,18,30,0.88))] shadow-[0_24px_60px_-42px_rgba(178,0,67,0.42)]'
                  : unlocked
                    ? 'border-white/[0.08] bg-[linear-gradient(180deg,rgba(18,22,35,0.94),rgba(10,13,22,0.82))] shadow-[0_22px_50px_-40px_rgba(0,0,0,0.8)] hover:-translate-y-0.5 hover:border-primary/26 hover:shadow-[0_28px_66px_-42px_rgba(178,0,67,0.34)]'
                    : 'cursor-not-allowed border-white/[0.06] bg-[linear-gradient(180deg,rgba(13,16,27,0.9),rgba(9,12,20,0.78))] opacity-60',
              )}
            >
              {/* status medallion */}
              {complete ? (
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-primary/20 ring-2 ring-primary">
                  <Check className="h-5 w-5 text-primary" />
                </span>
              ) : unlocked ? (
                <ProgressRing value={ratio} size={44} stroke={4} label={<span className="text-[10px] font-bold">{i + 1}</span>} />
              ) : (
                <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full bg-white/5 ring-1 ring-white/10">
                  <Lock className="h-4 w-4 text-white/30" />
                </span>
              )}

              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-white/30">
                    Milestone {i + 1}
                  </span>
                  <span
                    className={cn(
                      'rounded-full border px-1.5 py-0.5 text-[10px]',
                      complete
                        ? 'border-primary/20 bg-primary/14 text-primary-200'
                        : status === 'needs_remediation'
                          ? 'border-amber-400/18 bg-amber-400/15 text-amber-200'
                          : 'border-white/8 bg-white/[0.04] text-white/48',
                    )}
                  >
                    {STATUS_LABEL[status]}
                  </span>
                </div>
                <h3 className="mt-0.5 truncate font-medium text-white">{polishGeneratedLabel(sub.subskill_name)}</h3>
                <p className="mt-0.5 line-clamp-1 text-xs text-white/45">{sub.objective}</p>
              </div>
            </button>
          </motion.li>
        )
      })}
    </motion.ol>
  )
}
