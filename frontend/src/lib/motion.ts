/**
 * Shared Framer Motion presets so motion feels identical across both systems.
 * Import these variants/transitions instead of hand-rolling per-component
 * animations — that consistency is what makes A and B feel like one product.
 */
import type { Transition, Variants } from 'framer-motion'

export const spring: Transition = {
  type: 'spring',
  stiffness: 260,
  damping: 30,
  mass: 0.9,
}

export const easeOut: Transition = {
  duration: 0.5,
  ease: [0.22, 1, 0.36, 1],
}

/** Fade + rise — the default entrance for blocks and cards. */
export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: easeOut },
}

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: easeOut },
}

export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.96 },
  show: { opacity: 1, scale: 1, transition: spring },
}

/** Container that staggers its children's entrances. */
export const staggerContainer = (stagger = 0.07, delayChildren = 0): Variants => ({
  hidden: {},
  show: {
    transition: { staggerChildren: stagger, delayChildren },
  },
})

/** Page transition for route changes (wrap content in <PageTransition/>). */
export const pageTransition: Variants = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: easeOut },
  exit: { opacity: 0, y: -8, transition: { duration: 0.25, ease: 'easeIn' } },
}

/** Draw an SVG path/line from start to finish. */
export const drawLine: Variants = {
  hidden: { pathLength: 0, opacity: 0 },
  show: {
    pathLength: 1,
    opacity: 1,
    transition: { pathLength: { duration: 1.1, ease: 'easeInOut' }, opacity: { duration: 0.2 } },
  },
}
