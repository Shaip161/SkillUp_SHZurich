'use client'

import { useState } from 'react'
import { BookOpen } from 'lucide-react'
import type { GapResponse } from '@/lib/types'
import { cn } from '@/lib/utils'
import { SkillBadge } from './SkillBadge'

interface SkillGapProps {
  gap: GapResponse
}

export function SkillGap({ gap }: SkillGapProps) {
  const [toastVisible, setToastVisible] = useState(false)

  function handleStartLearning() {
    setToastVisible(true)
    setTimeout(() => setToastVisible(false), 2500)
  }

  const { missing_skills, matched_skills } = gap

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-base font-semibold text-white/80">Skill gap</h2>
        <p className="mt-0.5 text-sm text-white/40">
          {missing_skills.length === 0
            ? 'You have all required skills for this role.'
            : `You're missing ${missing_skills.length} required skill${missing_skills.length === 1 ? '' : 's'}.`}
        </p>
      </div>

      {matched_skills.length > 0 && (
        <div className="rounded-xl border border-teal-500/20 bg-teal-500/5 px-4 py-3">
          <p className="mb-2 text-xs uppercase tracking-wider text-teal-300/60">
            Already in your toolkit
          </p>
          <div className="flex flex-wrap gap-1.5">
            {matched_skills.map((s) => (
              <SkillBadge key={s} skill={s} variant="matched" />
            ))}
          </div>
        </div>
      )}

      {missing_skills.length > 0 && (
        <div className="space-y-2">
          {missing_skills.map((skill) => (
            <div
              key={skill}
              className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-white/5 px-4 py-3"
            >
              <SkillBadge skill={skill} variant="missing" />
              <button
                onClick={handleStartLearning}
                className="flex shrink-0 items-center gap-1.5 text-sm font-medium text-white/40 transition-colors hover:text-white"
              >
                <BookOpen className="h-3.5 w-3.5" />
                Start learning
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Coming-soon toast */}
      <div
        aria-live="polite"
        className={cn(
          'pointer-events-none fixed bottom-6 left-1/2 -translate-x-1/2 rounded-xl border border-white/20 bg-[#0d1528]/95 px-5 py-3 text-sm font-medium text-white shadow-xl backdrop-blur transition-all duration-300',
          toastVisible ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0',
        )}
      >
        Coming soon — personalised learning paths
      </div>
    </section>
  )
}
