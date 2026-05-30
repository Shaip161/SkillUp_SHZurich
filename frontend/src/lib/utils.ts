import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Clamp a number to a [min, max] range. */
export function clamp(value: number, min = 0, max = 1): number {
  return Math.min(max, Math.max(min, value))
}

/** Format a 0..1 ratio as a whole-number percentage string. */
export function formatPct(ratio: number): string {
  return `${Math.round(clamp(ratio) * 100)}%`
}

/** Kebab-case slug for ids/anchors. */
export function slugify(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '')
}

/** Initials for an avatar from a name or email. */
export function initials(value: string): string {
  const name = value.split('@')[0].replace(/[._-]+/g, ' ').trim()
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length === 0) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/** Light cleanup for generated UI labels so they read more like product copy. */
export function polishGeneratedLabel(value: string): string {
  return value
    .replace(/\s+—\s+/g, ', ')
    .replace(/\s*&\s*/g, ' and ')
    .replace(/,\s*Foundations$/i, ' Fundamentals')
    .replace(/,\s*Core Techniques$/i, ', Core Practice')
    .replace(/,\s*Applied Practice$/i, ', Applied Scenarios')
    .replace(/,\s*Integration$/i, ', Workflow Integration')
    .replace(/,\s*Mastery and Judgment$/i, ', Strategic Judgment')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

/** Small cleanup for sentence-style copy that uses dash separators too heavily. */
export function polishUiSentence(value: string): string {
  return value.replace(/\s+—\s+/g, ', ').replace(/\s{2,}/g, ' ').trim()
}
