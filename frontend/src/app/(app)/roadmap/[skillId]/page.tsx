'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useJourney, skillProgress } from '@/lib/store/journey'
import { SubskillList } from '@/components/learning/SubskillList'
import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { Reveal } from '@/components/ui/motion'
import { polishGeneratedLabel, polishUiSentence } from '@/lib/utils'

export default function SkillPage() {
  const router = useRouter()
  const params = useParams()
  const skillId = params.skillId as string
  const { state, ready } = useJourney()
  const { curriculum, progress } = state

  const skill = curriculum?.skills.find((s) => s.skill_id === skillId) ?? null

  useEffect(() => {
    if (ready && curriculum && !skill) router.replace('/roadmap')
    if (ready && !curriculum) router.replace('/matches')
  }, [ready, curriculum, skill, router])

  if (!curriculum || !skill) return null

  const ratio = skillProgress(skill, progress)

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      <Breadcrumb
        items={[
          { label: 'Roadmap', href: '/roadmap' },
          { label: polishGeneratedLabel(skill.skill_name) },
        ]}
      />

      <Reveal>
        <span className="inline-block rounded-full bg-white/5 px-2 py-0.5 text-[11px] capitalize text-white/45">
          {skill.difficulty_level}
        </span>
        <h1 className="mt-3 font-display text-3xl font-bold tracking-tight">{polishGeneratedLabel(skill.skill_name)}</h1>
        <p className="mt-2 text-white/55">{polishUiSentence(skill.description)}</p>
        <div className="mt-5 flex items-center gap-3">
          <ProgressBar value={ratio} className="max-w-xs" showLabel />
          <span className="text-xs text-white/40">
            {skill.subskills.filter((s) => progress[s.subskill_id]?.mastery_status === 'completed').length}
            /{skill.subskills.length} mastered
          </span>
        </div>
      </Reveal>

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-white/40">
          Milestones · complete in order
        </h2>
        <SubskillList skill={skill} progress={progress} />
      </div>
    </div>
  )
}
