'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import {
  ArrowRight,
  Award,
  BookOpen,
  Compass,
  Network,
  Sparkles,
  Target,
  TrendingUp,
  Trophy,
  Upload,
  Users,
} from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { PageTransition, Reveal, Stagger, StaggerItem } from '@/components/ui/motion'
import { useSession } from '@/lib/store/session'

interface LandingItem {
  icon: LucideIcon
  title: string
  body: string
}

interface JourneyMode {
  eyebrow: string
  title: string
  body: string
  details: string[]
  buttonLabel: string
  variant: 'primary' | 'accent' | 'secondary' | 'outline' | 'ghost'
  action: 'start' | 'login'
}

const HERO_HIGHLIGHTS = ['AI skill analysis', 'Matched roles', 'Personalized roadmap']

const STEPS: LandingItem[] = [
  {
    icon: Upload,
    title: 'Upload your CV',
    body: 'Start with your resume so Skill Up can extract your skills, strengths, and transferable experience.',
  },
  {
    icon: Sparkles,
    title: 'Review your matches',
    body: 'See which roles fit your profile best and where the biggest skill gaps still are.',
  },
  {
    icon: BookOpen,
    title: 'Choose a target role',
    body: 'Pick the role you want and turn its missing skills into a focused roadmap.',
  },
  {
    icon: Target,
    title: 'Start the roadmap',
    body: 'Build the skills that close the gap and move yourself toward stronger matches over time.',
  },
]

const PLATFORM_LAYERS: LandingItem[] = [
  {
    icon: Compass,
    title: 'AI skill analysis',
    body: 'Skill Up reads your CV and turns it into a clearer picture of what you already bring to the table.',
  },
  {
    icon: Network,
    title: 'Role matches with real gaps',
    body: 'Each suggested role shows where you fit today and which missing skills stand between you and the next step.',
  },
  {
    icon: Trophy,
    title: 'A roadmap built from the gap',
    body: 'Once you choose a role, the platform turns the skill gap into a structured path you can actually follow.',
  },
]

const MARKET_CONTEXT: LandingItem[] = [
  {
    icon: TrendingUp,
    title: 'Stop guessing what to learn next',
    body: 'Start from the gap between your current profile and the role you want instead of browsing generic course lists.',
  },
  {
    icon: Users,
    title: 'Make career moves with clearer evidence',
    body: 'Use your CV, job matches, and missing skills to decide what is worth learning next.',
  },
  {
    icon: Award,
    title: 'Turn insight into action',
    body: 'Go from analysis to roadmap in one connected flow instead of jumping between job boards and disconnected resources.',
  },
]

const JOURNEY_MODES: JourneyMode[] = [
  {
    eyebrow: 'Free analysis',
    title: 'Start with your CV',
    body: 'Upload your CV to get an AI skill analysis, role matches, and the missing skills behind each opportunity.',
    details: ['Works with the current upload flow', 'Takes PDF or DOCX files', 'Leads directly into matches and gap analysis'],
    buttonLabel: 'Start my free skill analysis',
    variant: 'accent',
    action: 'start',
  },
  {
    eyebrow: 'Come back anytime',
    title: 'Pick up where you left off',
    body: 'Sign in to revisit your matches, return to your roadmap, and keep building toward the role you want.',
    details: ['Keeps the current sign-in flow', 'Built for repeat visits', 'Returns you to the existing app experience'],
    buttonLabel: 'Login and continue',
    variant: 'secondary',
    action: 'login',
  },
]

const HOMEPAGE_VIDEO_SOURCES = [
  '/brand/hero-1.mp4',
  '/brand/hero-2.mp4',
  '/brand/hero-3.mp4',
  '/brand/hero-4.mp4',
  '/brand/hero-5.mp4',
]

const HERO_VIDEO_ROTATION_MS = 7200
const HERO_VIDEO_FADE_MS = 1400

function useHomepageVideoSources() {
  return HOMEPAGE_VIDEO_SOURCES
}

function LoopingVideoLayer({
  sources,
  className,
  rotate = true,
  preferredIndex = 0,
}: {
  sources: string[]
  className: string
  rotate?: boolean
  preferredIndex?: number
}) {
  const videoARef = useRef<HTMLVideoElement>(null)
  const videoBRef = useRef<HTMLVideoElement>(null)
  const [activePlayer, setActivePlayer] = useState<'A' | 'B'>('A')
  const [currentIndex, setCurrentIndex] = useState(0)

  const safeIndex = Math.min(preferredIndex, Math.max(sources.length - 1, 0))
  const shouldRotate = rotate && sources.length > 1

  useEffect(() => {
    setActivePlayer('A')
    setCurrentIndex(safeIndex)

    if (!shouldRotate) return

    const firstVideo = videoARef.current
    const secondVideo = videoBRef.current

    if (firstVideo) {
      firstVideo.src = sources[safeIndex]
      firstVideo.load()
      void firstVideo.play().catch(() => { })
    }

    if (secondVideo) {
      secondVideo.pause()
      secondVideo.removeAttribute('src')
      secondVideo.load()
    }
  }, [safeIndex, shouldRotate, sources])

  useEffect(() => {
    if (!shouldRotate) return

    let transitionTimeout: number | undefined
    const intervalId = window.setInterval(() => {
      const nextIndex = (currentIndex + 1) % sources.length
      const nextPlayer = activePlayer === 'A' ? 'B' : 'A'
      const nextVideo = nextPlayer === 'A' ? videoARef.current : videoBRef.current

      if (!nextVideo) return

      nextVideo.src = sources[nextIndex]
      nextVideo.load()
      void nextVideo.play().catch(() => { })

      transitionTimeout = window.setTimeout(() => {
        setActivePlayer(nextPlayer)
        setCurrentIndex(nextIndex)
      }, 140)
    }, HERO_VIDEO_ROTATION_MS)

    return () => {
      if (transitionTimeout) window.clearTimeout(transitionTimeout)
      window.clearInterval(intervalId)
    }
  }, [activePlayer, currentIndex, shouldRotate, sources])

  if (!shouldRotate) {
    return (
      <video
        key={sources[safeIndex]}
        autoPlay
        loop
        muted
        playsInline
        preload="metadata"
        className={className}
      >
        <source src={sources[safeIndex]} />
      </video>
    )
  }

  return (
    <>
      <video
        ref={videoARef}
        autoPlay
        loop
        muted
        playsInline
        preload="metadata"
        className={className}
        style={{
          opacity: activePlayer === 'A' ? 1 : 0,
          transition: `opacity ${HERO_VIDEO_FADE_MS}ms ease-in-out`,
        }}
      />
      <video
        ref={videoBRef}
        loop
        muted
        playsInline
        preload="metadata"
        className={className}
        style={{
          opacity: activePlayer === 'B' ? 1 : 0,
          transition: `opacity ${HERO_VIDEO_FADE_MS}ms ease-in-out`,
        }}
      />
    </>
  )
}

function HeroMediaBackground() {
  const sources = useHomepageVideoSources()
  const hasVideo = sources.length > 0

  return (
    <div className="absolute inset-0 overflow-hidden">
      {hasVideo && (
        <LoopingVideoLayer
          sources={sources}
          className="absolute inset-0 h-full w-full scale-[1.04] object-cover brightness-[0.34] saturate-[0.72]"
        />
      )}

      {!hasVideo && (
        <>
          <motion.div
            aria-hidden="true"
            className="absolute -left-12 top-[6%] h-[24rem] w-[24rem] rounded-full bg-primary/35 blur-[120px]"
            animate={{ x: [0, 36, 0], y: [0, 28, 0], scale: [1, 1.08, 1] }}
            transition={{ duration: 18, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            aria-hidden="true"
            className="absolute right-[-6%] top-[14%] h-[22rem] w-[22rem] rounded-full bg-accent/28 blur-[110px]"
            animate={{ x: [0, -28, 0], y: [0, 24, 0], scale: [1.04, 1, 1.04] }}
            transition={{ duration: 16, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            aria-hidden="true"
            className="absolute bottom-[-18%] left-[22%] h-[22rem] w-[30rem] rounded-full bg-white/[0.05] blur-[120px]"
            animate={{ x: [0, 22, 0], y: [0, -18, 0], opacity: [0.18, 0.34, 0.18] }}
            transition={{ duration: 20, repeat: Infinity, ease: 'easeInOut' }}
          />
          <motion.div
            aria-hidden="true"
            className="absolute inset-x-[-12%] top-[18%] h-[32%] bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.08),transparent)] blur-3xl"
            animate={{ x: ['-6%', '6%', '-6%'], opacity: [0.16, 0.3, 0.16] }}
            transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
          />
        </>
      )}

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_18%,rgba(178,0,67,0.18),transparent_28%),radial-gradient(circle_at_82%_18%,rgba(255,112,0,0.14),transparent_26%),radial-gradient(circle_at_50%_100%,rgba(255,255,255,0.04),transparent_42%)]" />
      <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.04),transparent_26%,transparent_72%,rgba(255,255,255,0.03))]" />
      <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(5,7,13,0.2)_0%,rgba(5,7,13,0.26)_28%,rgba(5,7,13,0.58)_68%,rgba(5,7,13,0.9)_100%)]" />
    </div>
  )
}

function SectionVideoAccent() {
  const sources = useHomepageVideoSources()
  const hasVideo = sources.length > 0

  return (
    <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-[44%] overflow-hidden lg:block">
      <div className="absolute inset-y-[10%] right-[-10%] w-[112%] overflow-hidden rounded-[2.4rem] border border-white/10 bg-white/[0.03] shadow-[0_28px_70px_-36px_rgba(0,0,0,0.85)]">
        {hasVideo ? (
          <LoopingVideoLayer
            sources={sources}
            rotate={false}
            preferredIndex={2}
            className="absolute inset-0 h-full w-full object-cover brightness-[0.24] saturate-[0.68]"
          />
        ) : (
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_25%,rgba(178,0,67,0.22),transparent_32%),radial-gradient(circle_at_70%_38%,rgba(255,112,0,0.18),transparent_28%),linear-gradient(180deg,rgba(12,16,28,0.88),rgba(7,10,18,0.96))]" />
        )}

        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(255,255,255,0.04),transparent_40%,rgba(255,255,255,0.02))]" />
        <div className="absolute inset-0 bg-[linear-gradient(180deg,rgba(7,10,18,0.1)_0%,rgba(7,10,18,0.5)_48%,rgba(7,10,18,0.9)_100%)]" />
      </div>

      <div className="absolute inset-y-0 left-0 w-[58%] bg-[linear-gradient(90deg,rgba(7,10,18,1)_0%,rgba(7,10,18,0.95)_30%,rgba(7,10,18,0.62)_58%,transparent_100%)]" />
      <div className="absolute inset-y-[12%] right-[-4%] w-[62%] rounded-full bg-primary/14 blur-[120px]" />
      <div className="absolute bottom-[6%] right-[16%] h-28 w-28 rounded-full bg-accent/12 blur-[80px]" />
    </div>
  )
}

export default function LandingPage() {
  const router = useRouter()
  const { session } = useSession()
  const start = () => router.push(session ? '/upload' : '/login')

  const routeToLogin = () => router.push('/login')
  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  return (
    <PageTransition className="flex flex-col gap-20 pb-8 sm:gap-28">
      <section className="relative left-1/2 -mt-6 w-screen -translate-x-1/2 overflow-hidden border-b border-white/[0.08] bg-base-950 shadow-elevated">
        <HeroMediaBackground />

        <div className="relative z-10 mx-auto flex min-h-[72svh] w-full max-w-6xl flex-col justify-center px-4 pb-12 pt-20 text-center sm:min-h-[calc(100vh-8rem)] sm:px-6 sm:pb-16 sm:pt-24 lg:pb-20">
          <Reveal className="mx-auto max-w-4xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/12 bg-black/25 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.24em] text-white/78 backdrop-blur-sm">
              <Sparkles className="h-3.5 w-3.5 text-primary-300" />
              AI-powered skill analysis and career matching
            </div>

            <h1 className="mx-auto mt-6 max-w-4xl font-display text-5xl font-bold leading-[1.04] tracking-tight text-white sm:text-6xl lg:text-[5rem]">
              See what&apos;s next
              <br />
              <span className="text-gradient">for your career.</span>
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base leading-8 text-white/78 sm:text-lg">
              Upload your CV to see your strongest skills, missing skills, and the roles you can grow into.
              Then build a roadmap tailored to the gap.
            </p>

            <div className="mt-10 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center">
              <Button size="lg" onClick={start} className="group sm:min-w-[250px]">
                Start my free skill analysis
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
              <Button size="lg" variant="secondary" onClick={() => scrollToSection('trajectory')}>
                See how it works
              </Button>
            </div>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-white/62">
              {HERO_HIGHLIGHTS.map((highlight) => (
                <span
                  key={highlight}
                  className="rounded-full border border-white/12 bg-black/20 px-3.5 py-2 backdrop-blur-sm"
                >
                  {highlight}
                </span>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <section id="trajectory" className="grid gap-10 lg:grid-cols-[0.82fr_1.18fr] lg:items-start">
        <Reveal className="max-w-xl">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-primary-200">How it works</p>
          <h2 className="mt-4 font-display text-3xl font-semibold leading-tight text-white sm:text-4xl">
            From CV upload to your next role in four steps.
          </h2>
          <p className="mt-5 text-base leading-8 text-white/60">
            Start with your profile, review the opportunities that fit, and then turn the missing skills into a plan.
          </p>
        </Reveal>

        <Stagger className="grid gap-4 sm:grid-cols-2" stagger={0.09}>
          {STEPS.map(({ icon: Icon, title, body }, index) => (
            <StaggerItem key={title} className="glass rounded-[1.6rem] p-6">
              <div className="flex items-start justify-between gap-4">
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-primary/25 to-accent/15 ring-1 ring-white/10">
                  <Icon className="h-5 w-5 text-primary-200" />
                </span>
                <span className="text-xs font-semibold uppercase tracking-[0.2em] text-white/35">
                  {String(index + 1).padStart(2, '0')}
                </span>
              </div>
              <h3 className="mt-5 font-display text-xl font-semibold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-7 text-white/55">{body}</p>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      <section className="relative overflow-hidden rounded-[2rem] border border-white/[0.08] bg-[linear-gradient(180deg,rgba(12,16,28,0.94),rgba(7,10,18,0.84))] px-6 py-8 sm:px-10 sm:py-10">
        <SectionVideoAccent />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,112,0,0.14),transparent_28%),radial-gradient(circle_at_bottom_left,rgba(178,0,67,0.2),transparent_30%)]" />
        <div className="relative z-10 grid gap-10 lg:grid-cols-[0.9fr_1.1fr] lg:items-center">
          <Reveal className="max-w-xl">
            <p className="text-sm font-medium uppercase tracking-[0.24em] text-accent-300">Inside the platform</p>
            <h2 className="mt-4 font-display text-3xl font-semibold leading-tight text-white sm:text-4xl">
              One flow from analysis to roadmap.
            </h2>
            <p className="mt-5 text-base leading-8 text-white/60">
              Skill Up connects CV analysis, role matching, and roadmap generation in one journey so you can move from insight to action faster.
            </p>

            <div className="mt-8 space-y-4">
              {PLATFORM_LAYERS.map(({ icon: Icon, title, body }) => (
                <div key={title} className="flex gap-4 rounded-[1.35rem] border border-white/10 bg-white/[0.04] p-4">
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-white/[0.05] ring-1 ring-white/10">
                    <Icon className="h-5 w-5 text-accent" />
                  </span>
                  <div>
                    <h3 className="font-display text-lg font-semibold text-white">{title}</h3>
                    <p className="mt-1.5 text-sm leading-6 text-white/55">{body}</p>
                  </div>
                </div>
              ))}
            </div>
          </Reveal>

          <Stagger className="grid gap-4" stagger={0.1}>
            <StaggerItem className="rounded-[1.65rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.06),rgba(255,255,255,0.02))] p-6 shadow-[0_24px_60px_-30px_rgba(0,0,0,0.7)]">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">Connected flow</p>
              <h3 className="mt-3 font-display text-2xl font-semibold text-white">From CV upload to roadmap without losing context</h3>
              <p className="mt-3 text-sm leading-7 text-white/58">
                Your analysis leads into matches, and your chosen role leads into a roadmap built around the skills you still need.
              </p>
            </StaggerItem>

            <div className="grid gap-4 sm:grid-cols-2">
              <StaggerItem className="glass rounded-[1.5rem] p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">Clear outputs</p>
                <h3 className="mt-3 font-display text-xl font-semibold text-white">Skills, gaps, and next steps</h3>
                <p className="mt-2 text-sm leading-6 text-white/55">
                  See what you already have, what each role still requires, and what the next step should be.
                </p>
              </StaggerItem>

              <StaggerItem className="glass rounded-[1.5rem] p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">Navigation intact</p>
                <h3 className="mt-3 font-display text-xl font-semibold text-white">The current app flow stays exactly where it is</h3>
                <p className="mt-2 text-sm leading-6 text-white/55">
                  Calls to action still lead into the existing sign-in, upload, matches, and roadmap routes.
                </p>
              </StaggerItem>
            </div>
          </Stagger>
        </div>
      </section>

      <section className="text-center">
        <Reveal className="mx-auto max-w-3xl">
          <p className="text-sm font-medium uppercase tracking-[0.24em] text-primary-200">Why this matters</p>
          <h2 className="mt-4 font-display text-3xl font-semibold leading-tight text-white sm:text-4xl">
            Most people do not need more generic courses. They need clearer next steps.
          </h2>
          <p className="mt-5 text-base leading-8 text-white/60">
            Skill Up starts from your current profile, shows the gap to a target role, and turns that gap into a plan you can follow.
          </p>
        </Reveal>

        <Stagger className="mt-10 grid gap-4 text-left md:grid-cols-3" stagger={0.08}>
          {MARKET_CONTEXT.map(({ icon: Icon, title, body }) => (
            <StaggerItem key={title} className="rounded-[1.55rem] border border-white/10 bg-white/[0.03] p-6">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-primary/18 to-accent/12 ring-1 ring-white/10">
                <Icon className="h-5 w-5 text-white" />
              </span>
              <h3 className="mt-5 font-display text-xl font-semibold text-white">{title}</h3>
              <p className="mt-2 text-sm leading-7 text-white/55">{body}</p>
            </StaggerItem>
          ))}
        </Stagger>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        {JOURNEY_MODES.map((mode) => (
          <Reveal key={mode.title} className="glass rounded-[1.85rem] p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-white/45">{mode.eyebrow}</p>
            <h2 className="mt-3 font-display text-2xl font-semibold text-white sm:text-[2rem]">{mode.title}</h2>
            <p className="mt-4 text-sm leading-7 text-white/58">{mode.body}</p>

            <div className="mt-6 space-y-3">
              {mode.details.map((detail) => (
                <div key={detail} className="flex items-start gap-3 text-sm text-white/60">
                  <span className="mt-2 h-1.5 w-1.5 rounded-full bg-accent" />
                  <span>{detail}</span>
                </div>
              ))}
            </div>

            <div className="mt-8">
              <Button
                size="lg"
                variant={mode.variant}
                onClick={mode.action === 'start' ? start : routeToLogin}
                className="group w-full justify-center sm:w-auto"
              >
                {mode.buttonLabel}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </div>
          </Reveal>
        ))}
      </section>

      <section className="relative overflow-hidden rounded-[2rem] border border-white/[0.08] bg-[linear-gradient(180deg,rgba(178,0,67,0.12),rgba(9,12,21,0.92))] px-6 py-12 text-center shadow-elevated sm:px-10 sm:py-16">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,112,0,0.18),transparent_24%),radial-gradient(circle_at_bottom_left,rgba(178,0,67,0.2),transparent_30%)]" />
        <Reveal className="relative z-10 mx-auto max-w-3xl">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-2xl border border-white/10 bg-white/[0.06]">
            <Award className="h-6 w-6 text-accent" />
          </div>
          <h2 className="mt-6 font-display text-3xl font-semibold leading-tight text-white sm:text-4xl">
            Ready to see what your CV can unlock?
          </h2>
          <p className="mt-5 text-base leading-8 text-white/65">
            Start with a free skill analysis, review your matches, and build a roadmap around the role you want.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" variant="accent" onClick={start} className="group min-w-[220px]">
              Start my free skill analysis
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button size="lg" variant="ghost" onClick={() => scrollToSection('trajectory')}>
              See how it works
            </Button>
          </div>
        </Reveal>
      </section>
    </PageTransition>
  )
}
