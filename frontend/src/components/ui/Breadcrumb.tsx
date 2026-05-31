'use client'

import Link from 'next/link'
import { ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface Crumb {
  label: string
  href?: string
}

export function Breadcrumb({ items, className }: { items: Crumb[]; className?: string }) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center gap-1 text-sm', className)}>
      {items.map((item, i) => {
        const last = i === items.length - 1
        return (
          <span key={`${item.label}-${i}`} className="flex items-center gap-1">
            {item.href && !last ? (
              <Link href={item.href} className="text-white/45 transition-colors hover:text-white/80">
                {item.label}
              </Link>
            ) : (
              <span className={last ? 'font-medium text-white' : 'text-white/45'}>{item.label}</span>
            )}
            {!last && <ChevronRight className="h-3.5 w-3.5 text-white/25" />}
          </span>
        )
      })}
    </nav>
  )
}
