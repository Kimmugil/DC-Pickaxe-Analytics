'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

export function NavLinks({ items }: { items: { href: string; label: string }[] }) {
  const path = usePathname()
  return (
    <nav className="order-last w-full sm:order-none sm:w-auto flex items-center gap-1 text-sm sm:flex-1 overflow-x-auto whitespace-nowrap -mx-1 px-1">
      {items.map(i => {
        const on = i.href === '/' ? path === '/' : path.startsWith(i.href)
        return (
          <Link key={i.href} href={i.href}
                className={`px-3 py-1.5 rounded-lg transition-colors ${on ? 'bg-slate-900 text-white font-medium' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'}`}>
            {i.label}
          </Link>
        )
      })}
    </nav>
  )
}
