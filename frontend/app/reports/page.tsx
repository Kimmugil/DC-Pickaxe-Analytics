import Link from 'next/link'
import { getWeeklyListWithInfo, getMonthlyListWithInfo } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { CAUSE_STYLE } from '@/lib/issueCategories'

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
  const [t, weeklyList, monthlyList] = await Promise.all([
    getTexts(),
    getWeeklyListWithInfo().catch(() => [] as Awaited<ReturnType<typeof getWeeklyListWithInfo>>),
    getMonthlyListWithInfo().catch(() => [] as Awaited<ReturnType<typeof getMonthlyListWithInfo>>),
  ])

  // 월별 주간 카드 그룹화
  const weeksByMonth = new Map<string, typeof weeklyList>()
  for (const w of weeklyList) {
    const ym = w.week_start.slice(0, 7)
    if (!weeksByMonth.has(ym)) weeksByMonth.set(ym, [])
    weeksByMonth.get(ym)!.push(w)
  }

  // 월간 요약 맵
  const monthlyMap = new Map(monthlyList.map(m => [m.month, m]))

  // 전체 월 목록 (주간 + 월간 union)
  const allMonths = [...new Set([
    ...Array.from(weeksByMonth.keys()),
    ...monthlyList.map(m => m.month),
  ])].sort((a, b) => b.localeCompare(a))

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

        {allMonths.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="space-y-10">
            {allMonths.map(ym => {
              const monthly = monthlyMap.get(ym)
              const weeks = weeksByMonth.get(ym) ?? []

              return (
                <section key={ym}>
                  {/* 월 헤더 */}
                  <div className="flex items-center gap-3 mb-4">
                    <h2 className="text-sm font-bold text-gray-800 whitespace-nowrap">
                      {fmtMonth(ym)}
                    </h2>
                    <div className="flex-1 h-px bg-gray-200" />
                    {weeks.length > 0 && (
                      <span className="text-xs text-gray-400 tabular-nums shrink-0">
                        {tp(t, 'reports.week_count', { count: weeks.length }, '{count}주')}
                      </span>
                    )}
                  </div>

                  {/* 월간 AI 요약 카드 */}
                  {monthly?.ai_summary && (
                    <div className="bg-purple-50 border border-purple-100 rounded-lg p-4 mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-semibold text-purple-700">
                          {t['reports.monthly_summary_label'] ?? '월간 종합 요약'}
                        </span>
                        <span className="text-[11px] text-purple-400 tabular-nums">
                          {tp(t, 'common.gallery_count', { count: monthly.gallery_count }, '{count}개')}
                        </span>
                      </div>
                      <p className="text-sm text-purple-900 leading-relaxed whitespace-pre-line">
                        {monthly.ai_summary}
                      </p>
                    </div>
                  )}

                  {/* 주간 카드 목록 */}
                  {weeks.length > 0 && (
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

                          {item.top_causes && item.top_causes.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {item.top_causes.map(cause => {
                                const style = CAUSE_STYLE[cause]
                                if (!style) return null
                                return (
                                  <span
                                    key={cause}
                                    className="text-[10px] px-1.5 py-0.5 rounded font-medium"
                                    style={{ backgroundColor: style.bg, color: style.text }}
                                  >
                                    {cause}
                                  </span>
                                )
                              })}
                            </div>
                          )}

                          <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                            <span className="text-[11px] text-gray-400">{item.week_start}</span>
                            <span className="text-gray-300 group-hover:text-gray-500 text-sm transition-colors">→</span>
                          </div>
                        </Link>
                      ))}
                    </div>
                  )}
                </section>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
