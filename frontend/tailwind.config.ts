import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#0a0f1e',
          900: '#0d1528',
          800: '#111d38',
        },
      },
    },
  },
  plugins: [],
}

export default config
