import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: {
    default: 'TransitionAI — Job matching for Switzerland',
    template: '%s | TransitionAI',
  },
  description:
    'Upload your CV and instantly see which Swiss IT, Engineering and Finance jobs match your skills — and exactly what to learn to close the gap.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <header className="sticky top-0 z-50 border-b border-white/10 bg-[#0a0f1e]/80 backdrop-blur">
          <div className="mx-auto flex h-14 max-w-6xl items-center px-4">
            <a href="/" className="flex flex-col leading-none">
              <span className="text-lg font-bold tracking-tight">
                Transition<span className="text-teal-400">AI</span>
              </span>
              <span className="text-[10px] uppercase tracking-widest text-white/35">
                Switzerland&nbsp;·&nbsp;IT&nbsp;·&nbsp;Engineering&nbsp;·&nbsp;Finance
              </span>
            </a>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-10">{children}</main>
      </body>
    </html>
  )
}
