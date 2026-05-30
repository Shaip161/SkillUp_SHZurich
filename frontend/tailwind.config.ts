import type { Config } from 'tailwindcss'

/**
 * Unified design system for the AI career-evolution platform.
 *
 * Tokens are driven by CSS custom properties declared in globals.css so the
 * same scale powers both System A (matchmaking) and System B (learning).
 * Palette philosophy: deep near-black base, layered surfaces, a signature
 * magenta primary + a vivid orange accent from the Skill Up brand system.
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
        // Primary brand accent (SDG Magenta)
        primary: {
          DEFAULT: '#b20043',
          50: '#fff1f7',
          100: '#ffd7e6',
          200: '#ffadc9',
          300: '#ff78a4',
          400: '#f1427d',
          500: '#b20043',
          600: '#930038',
          700: '#74002d',
        },
        // Secondary brand accent (Orange)
        accent: {
          DEFAULT: '#ff7000',
          300: '#ffa452',
          400: '#ff8a1f',
          500: '#ff7000',
          600: '#db6000',
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
        glow: '0 0 0 1px rgba(178,0,67,0.28), 0 0 32px -4px rgba(178,0,67,0.38)',
        'glow-accent': '0 0 0 1px rgba(255,112,0,0.28), 0 0 32px -4px rgba(255,112,0,0.35)',
        elevated: '0 24px 60px -20px rgba(0,0,0,0.65)',
      },
      backgroundImage: {
        'grid-faint':
          'linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px)',
        'radial-fade':
          'radial-gradient(ellipse 80% 60% at 50% -10%, rgba(178,0,67,0.14), transparent 70%)',
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
