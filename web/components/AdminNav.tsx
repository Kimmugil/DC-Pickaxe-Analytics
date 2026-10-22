'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const ITEMS = [
  { href: '/admin', label: '현황', icon: '◎' },
  { href: '/admin/galleries', label: '갤러리', icon: '▤' },
  { href: '/admin/texts', label: '화면 문구', icon: 'Aa' },
  { href: '/admin/rules', label: '규칙', icon: '⚑' },
  { href: '/admin/settings', label: '설정', icon: '⚙' },
]

export function AdminNav({ logout }: { logout: () => Promise<void> }) {
  const path = usePathname()
  return (
    <aside className="lg:w-52 lg:shrink-0">
      <nav className="flex gap-1 overflow-x-auto lg:sticky lg:top-20 lg:flex-col lg:overflow-visible">
        {ITEMS.map(i => {
          const on = i.href === '/admin' ? path === '/admin' : path.startsWith(i.href)
          return (
            <Link key={i.href} href={i.href}
                  className={`flex items-center gap-2.5 whitespace-nowrap rounded-lg px-3 py-2 text-sm transition-colors ${on ? 'bg-slate-900 font-semibold text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
              <span className="w-5 text-center text-xs opacity-70">{i.icon}</span>
              <span>{i.label}</span>
            </Link>
          )
        })}
        <div className="hidden lg:mt-4 lg:block lg:border-t lg:border-slate-200 lg:pt-3">
          <Link href="/" className="block rounded-lg px-3 py-2 text-sm text-slate-500 hover:bg-slate-100">← 사이트 보기</Link>
          <form action={logout}><button className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-500 hover:bg-slate-100">로그아웃</button></form>
        </div>
      </nav>
    </aside>
  )
}
