import Link from 'next/link'
import { getGalleryList } from '@/lib/data'
import { getTexts } from '@/lib/texts'

export async function GalleryFloatingNav() {
  const [list, t] = await Promise.all([
    getGalleryList().catch(() => [] as Awaited<ReturnType<typeof getGalleryList>>),
    getTexts(),
  ])

  const active = list.filter(g => g.recent_issue_days > 0 || g.latest_issue)
  if (!active.length) return null

  return (
    <div className="fixed right-3 top-1/2 -translate-y-1/2 z-20 w-40 hidden xl:block pointer-events-none">
      <div className="bg-white/90 backdrop-blur-sm border border-gray-200 rounded-lg shadow-sm p-2 pointer-events-auto">
        <p className="text-[10px] text-gray-400 font-medium px-1 pb-1.5 border-b border-gray-100 mb-1">
          {t['floating_nav.title'] ?? '갤러리 추적'}
        </p>
        <div className="space-y-px max-h-[60vh] overflow-y-auto">
          {active.map(g => (
            <Link
              key={g.id}
              href={`/gallery/${g.id}`}
              className="flex items-center justify-between px-1 py-0.5 rounded hover:bg-gray-50 transition-colors"
            >
              <span className="text-[11px] text-gray-700 truncate flex-1 min-w-0">{g.name}</span>
              <div className="flex flex-col items-end shrink-0 ml-1 gap-px">
                {g.recent_issue_days > 0 && (
                  <span className="text-[9px] text-amber-600 tabular-nums leading-tight">
                    이슈빈도 {g.recent_issue_days}일/4주
                  </span>
                )}
                {g.latest_issue && (
                  <span className={`text-[9px] font-medium tabular-nums leading-tight ${g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'}`}>
                    최근 {g.latest_issue.score}점
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
