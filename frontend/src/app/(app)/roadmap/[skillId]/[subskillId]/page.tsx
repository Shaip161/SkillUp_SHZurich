'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, PartyPopper } from 'lucide-react'
import { useJourney } from '@/lib/store/journey'
import { StageFlow } from '@/components/learning/StageFlow'
import { StageStepper } from '@/components/learning/StageStepper'
import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { Button } from '@/components/ui/Button'

export default function SubskillPage() {
  const router = useRouter()
  const params = useParams()
  const skillId = params.skillId as string
  const subskillId = params.subskillId as string
  const { state, ready } = useJourney()
  const { curriculum, progress } = state

  const skill = curriculum?.skills.find((s) => s.skill_id === skillId) ?? null
  const subskill = skill?.subskills.find((s) => s.subskill_id === subskillId) ?? null
  const p = progress[subskillId]

  useEffect(() => {
    if (!ready) return
    if (!curriculum) router.replace('/matches')
    else if (!skill || !subskill) router.replace('/roadmap')
    else if (p?.mastery_status === 'not_started') router.replace(`/roadmap/${skillId}`)
  }, [ready, curriculum, skill, subskill, p, skillId, router])

  if (!curriculum || !skill || !subskill || !p) return null

  const completed = p.mastery_status === 'completed'
  const idx = skill.subskills.findIndex((s) => s.subskill_id === subskillId)
  const nextSub = skill.subskills[idx + 1]
  const inRemediation =
    p.mastery_status === 'needs_remediation' ||
    p.mastery_status === 'retry_ready' ||
    p.current_stage === 'reflection'

  return (
    <div className="mx-auto max-w-2xl space-y-7">
      <Breadcrumb
        items={[
          { label: 'Roadmap', href: '/roadmap' },
          { label: skill.skill_name, href: `/roadmap/${skillId}` },
          { label: subskill.subskill_name },
        ]}
      />

      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">{subskill.subskill_name}</h1>
        <p className="mt-1 text-sm text-white/50">{subskill.objective}</p>
      </div>

      <div className="rounded-2xl border border-white/8 bg-white/[0.02] p-4">
        <StageStepper completed={p.completed_steps} current={p.current_stage} inRemediation={inRemediation} />
      </div>

      {completed ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring', stiffness: 240, damping: 20 }}
          className="relative overflow-hidden rounded-3xl border border-primary/30 bg-primary/[0.06] p-8 text-center"
        >
          <div className="pointer-events-none absolute inset-0 bg-radial-fade" />
          <span className="mx-auto grid h-16 w-16 place-items-center rounded-full bg-primary/20 ring-2 ring-primary">
            <PartyPopper className="h-7 w-7 text-primary" />
          </span>
          <h2 className="mt-4 font-display text-2xl font-bold">Milestone mastered</h2>
          <p className="mx-auto mt-2 max-w-sm text-sm text-white/55">
            You&apos;ve demonstrated real capability in {subskill.subskill_name.toLowerCase()}.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            {nextSub ? (
              <Button
                className="group"
                onClick={() => router.push(`/roadmap/${skillId}/${nextSub.subskill_id}`)}
              >
                Next milestone
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            ) : (
              <Button onClick={() => router.push('/roadmap')}>Back to roadmap</Button>
            )}
            <Button variant="ghost" onClick={() => router.push(`/roadmap/${skillId}`)}>
              View skill
            </Button>
          </div>
        </motion.div>
      ) : (
        <StageFlow skill={skill} subskill={subskill} progress={p} />
      )}
    </div>
  )
}
