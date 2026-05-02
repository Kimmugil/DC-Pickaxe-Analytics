import Link from 'next/link'

interface NavProps {
  back?: { href: string; label?: string }
  title?: string
  subtitle?: string
  active?: 'home' | 'reports'
}

export function Nav({ back, title, subtitle, active }: NavProps) {
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
                ← {back.label ?? '홈'}
              </Link>
              {title && (
                <div className="min-w-0 border-l border-gray-700 pl-3">
                  <p className="text-sm font-medium text-white truncate leading-tight">{title}</p>
                  {subtitle && <p className="text-[11px] text-gray-400 leading-tight">{subtitle}</p>}
                </div>
              )}
            </>
          ) : (
            <Link href="/" className="flex items-center gap-2">
              <span>⛏️</span>
              <div>
                <p className="text-sm font-semibold leading-tight">디씨곡괭이 정련소</p>
                <p className="text-[10px] text-gray-500 leading-tight hidden sm:block">
                  DC인사이드 키우기 장르 동향 분석
                </p>
              </div>
            </Link>
          )}
        </div>

        <nav className="flex items-center gap-0.5 text-xs shrink-0">
          <Link
            href="/"
            className={`px-3 py-1.5 rounded transition-colors ${
              active === 'home'
                ? 'text-white bg-gray-700'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            홈
          </Link>
          <Link
            href="/reports"
            className={`px-3 py-1.5 rounded transition-colors ${
              active === 'reports'
                ? 'text-white bg-gray-700'
                : 'text-gray-400 hover:text-white hover:bg-gray-800'
            }`}
          >
            리포트 목록
          </Link>
        </nav>

      </div>
    </header>
  )
}
