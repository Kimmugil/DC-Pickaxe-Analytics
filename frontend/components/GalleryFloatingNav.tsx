import Link from 'next/link'
import { getGalleryList, getCalendarData } from '@/lib/data'
import { getTexts } from '@/lib/texts'
import { MiniCalendar } from '@/components/MiniCalendar'

export async function GalleryFloatingNav() {
  const [list, t, calData] = await Promise.all([
    getGalleryList().catch(() => [] as Awaited<ReturnType<typeof getGalleryList>>),
    getTexts(),
    getCalendarData().catch(() => ({
      issuesByDate: {} as Record<string, { id: string; name: string; score: number; cause?: string }[]>,
      weeklyDates:  [] as string[],
    })),
  ])

  if (!list.length) return null

  return (
    <div className="fixed right-3 top-4 z-20 w-56 hidden xl:block pointer-events-none">
      <div className="bg-white/95 backdrop-blur-sm border border-gray-200 rounded-lg shadow-md pointer-events-auto flex flex-col"
        style={{ maxHeight: 'calc(100vh - 5rem)' }}>

        {/* 미니 캘린더 */}
        <div className="shrink-0">
          <MiniCalendar
            issuesByDate={calData.issuesByDate}
            weeklyDates={calData.weeklyDates}
          />
        </div>

        {/* 갤러리 목록 */}
        <div className="p-2.5 flex flex-col min-h-0 overflow-hidden">
          <p className="text-[11px] text-gray-400 font-semibold px-1 pb-1.5 border-b border-gray-100 mb-1.5 shrink-0">
            {t['floating_nav.title'] ?? '갤러리 추적'}
          </p>
          <div className="space-y-px overflow-y-auto">
            {list.map(g => (
              <Link
                key={g.id}
                href={`/gallery/${g.id}`}
                className="flex items-center justify-between px-1 py-1 rounded hover:bg-gray-50 transition-colors"
              >
                <span className="text-[12px] text-gray-800 truncate flex-1 min-w-0 font-medium">{g.name}</span>
                <div className="flex flex-col items-end shrink-0 ml-2 gap-0.5">
                  {g.recent_issue_days > 0 ? (
                    <span className="text-[10px] text-amber-600 tabular-nums leading-tight whitespace-nowrap">
                      {t['floating_nav.issue_freq']?.replace('{count}', String(g.recent_issue_days)) ?? `이슈빈도 ${g.recent_issue_days}일/4주`}
                    </span>
                  ) : (
                    <span className="text-[10px] text-gray-300 leading-tight">{t['floating_nav.no_issue'] ?? '이슈 없음'}</span>
                  )}
                  {g.latest_issue && (
                    <span className={`text-[10px] font-semibold tabular-nums leading-tight ${g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'}`}>
                      {t['floating_nav.recent_score']?.replace('{score}', String(g.latest_issue.score)) ?? `최근 ${g.latest_issue.score}점`}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>

      </div>
    </div>
  )
}
