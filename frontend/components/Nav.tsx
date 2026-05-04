import Link from 'next/link'
import { getTexts } from '@/lib/texts'

interface NavProps {
  back?: { href: string; label?: string }
  title?: string
  subtitle?: string
  active?: 'home' | 'reports' | 'daily' | 'gallery' | 'timeline' | 'admin'
}

export async function Nav({ back, title, subtitle, active }: NavProps) {
  const t = await getTexts()

  return (
    <header className="bg-gray-900 text-white sticky top-0 z-10">
      <div className="max-w-6xl mx-auto px-4 h-12 flex items-center gap-4">

        <div className="flex items-center gap-3 flex-1 min-w-0">
          {back ? (
            <>
              <Link
                href={back.href}
                className="text-gray-400 hover:text-white text-sm shrink-0 transition-colors"
              >
                ← {back.label ?? t['nav.back'] ?? '뒤로'}
              </Link>
              {title && (
                <div className="min-w-0 border-l border-gray-700 pl-3">
                  <p className="text-sm font-medium text-white truncate leading-tight">{title}</p>
                  {subtitle && <p className="text-[11px] text-gray-400 leading-tight">{subtitle}</p>}
                </div>
              )}
            </>
          ) : (
            <Link href="/" className="flex items-center gap-2 shrink-0">
              <span>⛏️</span>
              <div>
                <p className="text-sm font-semibold leading-tight">
                  {t['nav.title'] ?? '디씨곡괭이 정련소'}
                </p>
                <p className="text-[10px] text-gray-500 leading-tight hidden sm:block">
                  {t['nav.subtitle'] ?? 'DC인사이드 키우기 장르 동향 분석'}
                </p>
              </div>
            </Link>
          )}
        </div>

        <nav className="flex items-center gap-0.5 text-xs">
          {[
            { href: '/',         key: 'home',     label: t['nav.home']     ?? '홈' },
            { href: '/gallery',  key: 'gallery',  label: t['nav.gallery']  ?? '갤러리별 리포트' },
            { href: '/timeline', key: 'timeline', label: t['nav.timeline'] ?? '타임라인' },
          ].map(item => (
            <Link
              key={item.key}
              href={item.href}
              className={`px-3 py-1.5 rounded transition-colors ${
                active === item.key
                  ? 'text-white bg-gray-700'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              }`}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href="/admin"
            className={`ml-3 px-2.5 py-1.5 rounded transition-colors text-[11px] ${
              active === 'admin'
                ? 'text-gray-300 bg-gray-800'
                : 'text-gray-600 hover:text-gray-400 hover:bg-gray-800'
            }`}
          >
            {t['nav.admin'] ?? '관리자'}
          </Link>
        </nav>

      </div>
    </header>
  )
}
