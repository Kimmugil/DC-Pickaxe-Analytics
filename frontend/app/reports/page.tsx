import Link from 'next/link'
import { getWeeklyListWithInfo } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}/${day}`
}

function fmtMonth(yearMonth: string) {
  const [y, m] = yearMonth.split('-').map(Number)
  return `${y}년 ${m}월`
}

export default async function ReportsPage() {
  const [t, list] = await Promise.all([
    getTexts(),
    getWeeklyListWithInfo().catch(() => [] as Awaited<ReturnType<typeof getWeeklyListWithInfo>>),
  ])

  // 월별 그룹화
  const byMonth = new Map<string, typeof list>()
  for (const w of list) {
    const ym = w.week_start.slice(0, 7)
    if (!byMonth.has(ym)) byMonth.set(ym, [])
    byMonth.get(ym)!.push(w)
  }
  const monthGroups = Array.from(byMonth.entries()).sort((a, b) => b[0].localeCompare(a[0]))

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="reports" />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">

        <div>
          <h1 className="text-lg font-bold text-gray-900">
            {t['reports.page_title'] ?? '종합 리포트'}
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            {t['reports.page_subtitle'] ?? '월별·주별 갤러리 동향 아카이브'}
          </p>
        </div>

        {monthGroups.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="space-y-10">
            {monthGroups.map(([ym, weeks]) => (
              <section key={ym}>
                {/* 월 헤더 */}
                <div className="flex items-center gap-3 mb-4">
                  <h2 className="text-sm font-bold text-gray-800 whitespace-nowrap">
                    {fmtMonth(ym)}
                  </h2>
                  <div className="flex-1 h-px bg-gray-200" />
                  <span className="text-xs text-gray-400 tabular-nums shrink-0">
                    {tp(t, 'reports.week_count', { count: weeks.length }, '{count}주')}
                  </span>
                </div>

                {/* 주간 카드 목록 */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {weeks.map(item => (
                    <Link
                      key={item.week_start}
                      href={`/weekly/${item.week_start}`}
                      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors group flex flex-col gap-3"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-sm font-semibold text-gray-900">
                          {fmtShort(item.week_start)} ~ {fmtShort(item.week_end)}
                        </span>
                        <span className="text-xs text-gray-400 shrink-0 tabular-nums">
                          {tp(t, 'common.gallery_count', { count: item.gallery_count }, '{count}개')}
                        </span>
                      </div>

                      {item.ai_summary ? (
                        <p className="text-xs text-gray-600 leading-relaxed line-clamp-4 flex-1">
                          {item.ai_summary}
                        </p>
                      ) : (
                        <p className="text-xs text-gray-300 flex-1">
                          {t['common.no_summary'] ?? '요약 없음'}
                        </p>
                      )}

                      <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                        <span className="text-[11px] text-gray-400">{item.week_start}</span>
                        <span className="text-gray-300 group-hover:text-gray-500 text-sm transition-colors">→</span>
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
