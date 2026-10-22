import Link from 'next/link'
import { getTexts, T } from '@/lib/texts'
import { isAdmin } from '@/lib/auth'
import { NavLinks } from './NavLinks'

export async function Nav() {
  const t = await getTexts()
  const admin = await isAdmin()
  const items = [
    { href: '/', label: T(t, 'nav.home') },
    { href: '/gallery', label: T(t, 'nav.gallery') },
  ]
  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="max-w-6xl mx-auto px-4 py-2.5 flex flex-wrap items-center gap-x-5 gap-y-2">
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-slate-900 text-base text-white">⛏</span>
          <span className="leading-tight">
            <span className="block text-sm font-bold text-slate-900">{T(t, 'nav.title')}</span>
            <span className="hidden sm:block text-[11px] text-slate-400">{T(t, 'nav.subtitle')}</span>
          </span>
        </Link>
        <NavLinks items={items} />
        <div className="ml-auto flex items-center gap-4 text-xs text-slate-400 sm:ml-0">
          <Link href="/about" className="hover:text-slate-700">{T(t, 'nav.about')}</Link>
          <Link href={admin ? '/admin' : '/admin/login'} className="hover:text-slate-700">{admin ? '관리자 ›' : T(t, 'nav.admin')}</Link>
        </div>
      </div>
    </header>
  )
}
