import type { Config } from 'tailwindcss'

/**
 * Unified design system for the AI career-evolution platform.
 *
 * Tokens are driven by CSS custom properties declared in globals.css so the
 * same scale powers both System A (matchmaking) and System B (learning).
 * Palette philosophy: deep near-black base, layered surfaces, an emerald
 * "growth" primary + an electric cyan "intelligence" accent. No AI-purple.
 */
const config: Config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Base background layers (deepest -> raised surfaces)
        base: {
          950: '#05070d',
          900: '#070b16',
          800: '#0b1120',
          700: '#111a2e',
          600: '#18233b',
        },
        // Primary "growth" accent (evolved from the original teal)
        primary: {
          DEFAULT: '#34e0a1',
          50: '#e8fff6',
          100: '#c4ffe9',
          200: '#8ff7d3',
          300: '#55ecbb',
          400: '#34e0a1',
          500: '#16c489',
          600: '#0b9e6e',
          700: '#0a7a57',
        },
        // Secondary "intelligence" accent (electric cyan)
        accent: {
          DEFAULT: '#38bdf8',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
        },
        // legacy alias kept so any leftover navy-* utility still resolves
        navy: {
          950: '#05070d',
          900: '#070b16',
          800: '#0b1120',
        },
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        display: ['var(--font-display)', 'var(--font-sans)', 'sans-serif'],
        mono: ['var(--font-mono)', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(52,224,161,0.25), 0 0 32px -4px rgba(52,224,161,0.35)',
        'glow-accent': '0 0 0 1px rgba(56,189,248,0.25), 0 0 32px -4px rgba(56,189,248,0.35)',
        elevated: '0 24px 60px -20px rgba(0,0,0,0.65)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px)',
        'radial-fade':
          'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(52,224,161,0.12), transparent 70%)',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '0.6', transform: 'scale(1)' },
          '50%': { opacity: '1', transform: 'scale(1.04)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
        'spin-slow': {
          to: { transform: 'rotate(360deg)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.5s cubic-bezier(0.22,1,0.36,1) both',
        shimmer: 'shimmer 2s linear infinite',
        'pulse-glow': 'pulse-glow 3s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
        'spin-slow': 'spin-slow 14s linear infinite',
      },
    },
  },
  plugins: [],
}

export default config
