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
    <div className="fixed right-3 top-1/2 -translate-y-1/2 z-20 w-56 hidden xl:block pointer-events-none">
      <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg shadow-md p-2.5 pointer-events-auto">
        <p className="text-[11px] text-gray-400 font-semibold px-1 pb-1.5 border-b border-gray-100 mb-1.5">
          {t['floating_nav.title'] ?? '갤러리 추적'}
        </p>
        <div className="space-y-0.5 max-h-[65vh] overflow-y-auto">
          {active.map(g => (
            <Link
              key={g.id}
              href={`/gallery/${g.id}`}
              className="flex items-center justify-between px-1 py-1 rounded hover:bg-gray-50 transition-colors"
            >
              <span className="text-[12px] text-gray-800 truncate flex-1 min-w-0 font-medium">{g.name}</span>
              <div className="flex flex-col items-end shrink-0 ml-2 gap-0.5">
                {g.recent_issue_days > 0 && (
                  <span className="text-[10px] text-amber-600 tabular-nums leading-tight whitespace-nowrap">
                    이슈빈도 {g.recent_issue_days}일/4주
                  </span>
                )}
                {g.latest_issue && (
                  <span className={`text-[10px] font-semibold tabular-nums leading-tight ${g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'}`}>
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
