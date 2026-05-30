'use client'

import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { ArrowRight, Sparkles, Compass, Network, Trophy } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Reveal, Stagger, StaggerItem } from '@/components/ui/motion'
import { useSession } from '@/lib/store/session'

const PILLARS = [
  { icon: Compass, title: 'Match', body: 'See the roles you could grow into — ranked by real compatibility, not keywords.' },
  { icon: Network, title: 'Generate', body: 'An AI composes a personalized evolution path from your exact skill gaps.' },
  { icon: Trophy, title: 'Evolve', body: 'Progress through adaptive stages until the future role is genuinely yours.' },
]

export default function LandingPage() {
  const router = useRouter()
  const { session } = useSession()
  const start = () => router.push(session ? '/upload' : '/login')

  return (
    <div className="flex flex-col items-center">
      {/* Hero */}
      <section className="relative w-full pt-16 sm:pt-24">
        <Reveal className="mx-auto max-w-3xl text-center">
          <motion.span
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3.5 py-1.5 text-xs font-medium text-primary-200"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Your career, intelligently evolved
          </motion.span>

          <h1 className="mt-6 font-display text-5xl font-bold leading-[1.05] tracking-tight sm:text-7xl">
            Become the next
            <br />
            <span className="text-gradient">version of yourself.</span>
          </h1>

          <p className="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-white/55">
            Not a course catalog. An AI operating system that maps the distance between who you are
            today and the role you want — then closes it, step by step.
          </p>

          <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" onClick={start} className="group">
              Begin your evolution
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button size="lg" variant="ghost" onClick={() => router.push('/login')}>
              I already have an account
            </Button>
          </div>
        </Reveal>

        {/* Ambient orbit visual */}
        <div className="pointer-events-none mx-auto mt-16 h-px max-w-2xl bg-gradient-to-r from-transparent via-primary/40 to-transparent" />
      </section>

      {/* Pillars */}
      <Stagger className="mt-16 grid w-full max-w-5xl gap-4 sm:grid-cols-3" stagger={0.1}>
        {PILLARS.map(({ icon: Icon, title, body }) => (
          <StaggerItem
            key={title}
            className="group rounded-2xl border border-white/10 bg-white/[0.03] p-6 transition-colors hover:border-primary/30"
          >
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/10 ring-1 ring-white/10">
              <Icon className="h-5 w-5 text-primary" />
            </span>
            <h3 className="mt-4 font-display text-lg font-semibold">{title}</h3>
            <p className="mt-1.5 text-sm leading-relaxed text-white/50">{body}</p>
          </StaggerItem>
        ))}
      </Stagger>
    </div>
  )
}
