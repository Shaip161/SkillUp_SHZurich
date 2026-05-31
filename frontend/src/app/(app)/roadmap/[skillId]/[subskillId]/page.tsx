'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, PartyPopper } from 'lucide-react'
import { CommunityFeed } from '@/components/community/CommunityFeed'
import { useJourney } from '@/lib/store/journey'
import { StageFlow } from '@/components/learning/StageFlow'
import { StageStepper } from '@/components/learning/StageStepper'
import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { Button } from '@/components/ui/Button'
import { polishGeneratedLabel } from '@/lib/utils'

export default function SubskillPage() {
  const router = useRouter()
  const params = useParams()
  const [activeTab, setActiveTab] = useState<'course' | 'community'>('course')
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
  const displaySkillName = polishGeneratedLabel(skill.skill_name)
  const displaySubskillName = polishGeneratedLabel(subskill.subskill_name)

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <Breadcrumb
        items={[
          { label: 'Roadmap', href: '/roadmap' },
          { label: displaySkillName, href: `/roadmap/${skillId}` },
          { label: displaySubskillName },
        ]}
      />

      <div className="max-w-3xl">
        <h1 className="font-display text-2xl font-bold tracking-tight">{displaySubskillName}</h1>
        <p className="mt-1 text-sm text-white/50">{subskill.objective}</p>
      </div>

      <div className="rounded-3xl border border-white/10 bg-white/[0.02] p-2">
        <div className="grid gap-2 sm:grid-cols-2" role="tablist" aria-label="Course page sections">
          {[
            { id: 'course' as const, label: 'Course', helper: 'Stages and validation' },
            { id: 'community' as const, label: 'Community', helper: 'Peer discussion feed' },
          ].map((tab) => {
            const selected = activeTab === tab.id

            return (
              <button
                key={tab.id}
                id={`subskill-tab-${tab.id}`}
                type="button"
                role="tab"
                aria-selected={selected}
                aria-controls={`subskill-panel-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`rounded-[20px] border px-4 py-3 text-left transition ${selected
                    ? 'border-primary/30 bg-gradient-to-r from-primary/18 via-primary/10 to-accent/12 text-white shadow-[0_12px_40px_-24px_rgba(178,0,67,0.75)]'
                    : 'border-transparent text-white/58 hover:border-white/10 hover:bg-white/[0.03] hover:text-white/80'
                  }`}
              >
                <span className="block text-sm font-semibold tracking-tight">{tab.label}</span>
                <span className={`mt-1 block text-xs ${selected ? 'text-white/68' : 'text-white/42'}`}>
                  {tab.helper}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      <section
        id="subskill-panel-course"
        role="tabpanel"
        aria-labelledby="subskill-tab-course"
        hidden={activeTab !== 'course'}
        className="space-y-6"
      >
        <div className="rounded-3xl border border-white/8 bg-white/[0.02] p-4 lg:p-5">
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
              You&apos;ve demonstrated real capability in {displaySubskillName.toLowerCase()}.
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
      </section>

      <section
        id="subskill-panel-community"
        role="tabpanel"
        aria-labelledby="subskill-tab-community"
        hidden={activeTab !== 'community'}
      >
        <CommunityFeed skillName={displaySkillName} subskillName={displaySubskillName} />
      </section>
    </div>
  )
}
