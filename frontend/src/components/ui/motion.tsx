'use client'

import { motion, type HTMLMotionProps } from 'framer-motion'
import { fadeUp, pageTransition, staggerContainer } from '@/lib/motion'

/** In-view reveal (fade + rise). Use for sections/cards as they scroll in. */
export function Reveal({
  children,
  delay = 0,
  once = true,
  ...props
}: HTMLMotionProps<'div'> & { delay?: number; once?: boolean }) {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      whileInView="show"
      viewport={{ once, margin: '-60px' }}
      transition={{ delay }}
      {...props}
    >
      {children}
    </motion.div>
  )
}

/** Staggers direct children that use the `fadeUp` (or item) variant. */
export function Stagger({
  children,
  stagger = 0.07,
  delayChildren = 0,
  ...props
}: HTMLMotionProps<'div'> & { stagger?: number; delayChildren?: number }) {
  return (
    <motion.div
      variants={staggerContainer(stagger, delayChildren)}
      initial="hidden"
      animate="show"
      {...props}
    >
      {children}
    </motion.div>
  )
}

/** Item for use inside <Stagger/>. */
export function StaggerItem({ children, ...props }: HTMLMotionProps<'div'>) {
  return (
    <motion.div variants={fadeUp} {...props}>
      {children}
    </motion.div>
  )
}

/** Wraps a page/route content for an entrance transition. */
export function PageTransition({ children, ...props }: HTMLMotionProps<'div'>) {
  return (
    <motion.div variants={pageTransition} initial="hidden" animate="show" {...props}>
      {children}
    </motion.div>
  )
}
