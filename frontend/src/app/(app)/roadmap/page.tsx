'use client'

import { useEffect, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowRight, Sparkles } from 'lucide-react'
import { useJourney, overallProgress } from '@/lib/store/journey'
import { RoadmapPath } from '@/components/learning/RoadmapPath'
import { ProgressRing } from '@/components/ui/ProgressRing'
import { Button } from '@/components/ui/Button'
import { Reveal } from '@/components/ui/motion'
import { polishUiSentence } from '@/lib/utils'

export default function RoadmapPage() {
  const router = useRouter()
  const { state, ready } = useJourney()
  const { curriculum, progress } = state

  useEffect(() => {
    if (ready && !curriculum) router.replace('/matches')
  }, [ready, curriculum, router])

  const overall = overallProgress(curriculum, progress)

  // Find the next thing to do: first subskill that isn't completed.
  const next = useMemo(() => {
    if (!curriculum) return null
    for (const skill of curriculum.skills) {
      for (const sub of skill.subskills) {
        if (progress[sub.subskill_id]?.mastery_status !== 'completed') {
          return { skillId: skill.skill_id, subskillId: sub.subskill_id, name: sub.subskill_name }
        }
      }
    }
    return null
  }, [curriculum, progress])

  if (!curriculum) return null

  const done = overall >= 1

  return (
    <div className="space-y-12">
      {/* Hero / progression header (Step 8) */}
      <Reveal className="relative overflow-hidden rounded-[32px] border border-white/[0.07] bg-[linear-gradient(135deg,rgba(21,25,39,0.94),rgba(10,13,23,0.82))] p-6 shadow-[0_36px_100px_-58px_rgba(0,0,0,0.9)] sm:p-8">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,112,0,0.12),transparent_28%),radial-gradient(circle_at_top_left,rgba(178,0,67,0.18),transparent_34%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent_40%)]" />
        <div className="relative flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.2em] text-primary/70">
              Your evolution path
            </p>
            <h1 className="mt-2 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              {polishUiSentence(curriculum.target_role.title)}
            </h1>
            <p className="mt-2 max-w-md text-sm text-white/55">
              {done
                ? 'Every skill is mastered. You have fully grown into this role.'
                : `${curriculum.skills.length} skills compose this transformation. ${Math.round(overall * 100)}% complete.`}
            </p>
            {next && (
              <Button
                className="mt-5 group"
                onClick={() => router.push(`/roadmap/${next.skillId}/${next.subskillId}`)}
              >
                <Sparkles className="h-4 w-4" />
                {overall === 0 ? 'Start your journey' : 'Continue learning'}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            )}
          </div>
          <div className="flex flex-col items-center">
            <ProgressRing value={overall} size={104} stroke={8} />
            <span className="mt-2 text-xs uppercase tracking-wider text-white/40">
              Role readiness
            </span>
          </div>
        </div>
      </Reveal>

      {/* The journey map (Step 5) */}
      <RoadmapPath curriculum={curriculum} progress={progress} overall={overall} />
    </div>
  )
}
