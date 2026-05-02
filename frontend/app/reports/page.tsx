import Link from 'next/link'
import { getDailyIssueList, getWeeklyListWithInfo } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}/${day}`
}

function fmtFull(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

export default async function ReportsPage() {
  const [t, dailyList, weeklyList] = await Promise.all([
    getTexts(),
    getDailyIssueList().catch(() => [] as Awaited<ReturnType<typeof getDailyIssueList>>),
    getWeeklyListWithInfo().catch(() => [] as Awaited<ReturnType<typeof getWeeklyListWithInfo>>),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="weekly" />

      <main className="max-w-5xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

          {/* ── 주간 리포트 ── */}
          <section>
            <div className="flex items-baseline justify-between mb-3">
              <h2 className="text-xs font-medium text-gray-400">
                {t['reports.section_weekly'] ?? '주간 리포트'}
              </h2>
              <Link href="/weekly" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
                {t['reports.link_weekly'] ?? '전체 목록 →'}
              </Link>
            </div>

            {weeklyList.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-10">
                {t['common.no_data'] ?? '데이터 없음'}
              </p>
            ) : (
              <div className="space-y-1.5">
                {weeklyList.map(item => (
                  <Link
                    key={item.week_start}
                    href={`/weekly/${item.week_start}`}
                    className="block bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-gray-900">
                        {fmtShort(item.week_start)} ~ {fmtFull(item.week_end)}
                      </span>
                      <span className="text-xs text-gray-400 shrink-0">
                        {tp(t, 'common.gallery_count', { count: item.gallery_count }, '{count}개 갤러리')}
                      </span>
                    </div>
                    {item.ai_summary && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-1">{item.ai_summary}</p>
                    )}
                  </Link>
                ))}
              </div>
            )}
          </section>

          {/* ── 일간 이슈 ── */}
          <section>
            <div className="flex items-baseline justify-between mb-3">
              <h2 className="text-xs font-medium text-gray-400">
                {t['reports.section_daily'] ?? '일간 이슈'}
              </h2>
              <Link href="/daily" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
                {t['reports.link_daily'] ?? '전체 목록 →'}
              </Link>
            </div>

            {dailyList.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-10">
                {t['common.no_data'] ?? '데이터 없음'}
              </p>
            ) : (
              <div className="space-y-1.5">
                {dailyList.map(item => {
                  const hasHighIssue = item.max_score >= 7
                  return (
                    <Link
                      key={item.date}
                      href={`/daily/${item.date}`}
                      className="block bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-gray-900">{fmtFull(item.date)}</span>
                        <span className="text-xs text-gray-400 shrink-0">
                          {tp(t, 'common.issue_count', { count: item.issue_count }, '이슈 {count}개')}
                          {item.borderline_count > 0 && (
                            <> · {tp(t, 'common.borderline_count', { count: item.borderline_count }, '경계 {count}개')}</>
                          )}
                        </span>
                      </div>
                      {item.galleries.length > 0 && (
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          {item.galleries.map(g => (
                            <span key={g.name} className="text-xs text-gray-500">
                              {g.name}{' '}
                              <span className={`tabular-nums font-medium ${hasHighIssue ? 'text-red-500' : 'text-orange-500'}`}>
                                {g.score}점
                              </span>
                            </span>
                          ))}
                        </div>
                      )}
                    </Link>
                  )
                })}
              </div>
            )}
          </section>

        </div>
      </main>
    </div>
  )
}
