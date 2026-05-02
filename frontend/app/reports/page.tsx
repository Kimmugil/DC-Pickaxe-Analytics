import Link from 'next/link'
import { getDailyIssueList, getWeeklyListWithInfo } from '@/lib/data'
import { Nav } from '@/components/Nav'

function fmt(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

export default async function ReportsPage() {
  const [dailyList, weeklyList] = await Promise.all([
    getDailyIssueList().catch(() => [] as Awaited<ReturnType<typeof getDailyIssueList>>),
    getWeeklyListWithInfo().catch(() => [] as Awaited<ReturnType<typeof getWeeklyListWithInfo>>),
  ])

  type WeeklyItem = {
    type: 'weekly'
    sortKey: string
    week_start: string
    week_end: string
    gallery_count: number
    ai_summary: string
  }
  type DailyItem = {
    type: 'daily'
    sortKey: string
    date: string
    issue_count: number
    borderline_count: number
    max_score: number
    top_galleries: { name: string; score: number }[]
  }

  const combined: (WeeklyItem | DailyItem)[] = [
    ...weeklyList.map(w => ({ type: 'weekly' as const, sortKey: w.week_start, ...w })),
    ...dailyList.map(d => ({ type: 'daily' as const, sortKey: d.date, ...d })),
  ].sort((a, b) => b.sortKey.localeCompare(a.sortKey))

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="reports" />

      <main className="max-w-4xl mx-auto px-4 py-6">
        <div className="flex items-baseline justify-between mb-5">
          <h1 className="text-base font-semibold text-gray-900">리포트 목록</h1>
          <div className="flex items-center gap-3 text-xs text-gray-400">
            <Link href="/weekly" className="hover:text-gray-600 transition-colors">
              주간 목록
            </Link>
            <Link href="/daily" className="hover:text-gray-600 transition-colors">
              일간 목록
            </Link>
          </div>
        </div>

        {combined.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">데이터 없음</p>
        ) : (
          <div className="space-y-1.5">
            {combined.map(item => {
              if (item.type === 'weekly') {
                return (
                  <Link
                    key={`w-${item.week_start}`}
                    href={`/weekly/${item.week_start}`}
                    className="flex items-start gap-3 bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
                  >
                    <span className="text-[11px] font-medium text-blue-600 bg-blue-50 px-2 py-0.5 rounded mt-0.5 shrink-0 tabular-nums">
                      주간
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-gray-900">
                          {fmt(item.week_start)} ~ {fmt(item.week_end)}
                        </span>
                        <span className="text-xs text-gray-400 shrink-0">
                          {item.gallery_count}개 갤러리
                        </span>
                      </div>
                      {item.ai_summary && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-1">
                          {item.ai_summary}
                        </p>
                      )}
                    </div>
                    <span className="text-gray-300 group-hover:text-gray-500 text-sm shrink-0 self-center transition-colors">
                      →
                    </span>
                  </Link>
                )
              }

              const hasHighIssue = item.max_score >= 7
              return (
                <Link
                  key={`d-${item.date}`}
                  href={`/daily/${item.date}`}
                  className="flex items-start gap-3 bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
                >
                  <span
                    className={`text-[11px] font-medium px-2 py-0.5 rounded mt-0.5 shrink-0 ${
                      hasHighIssue
                        ? 'text-red-600 bg-red-50'
                        : 'text-orange-600 bg-orange-50'
                    }`}
                  >
                    이슈
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-gray-900">{fmt(item.date)}</span>
                      <span className="text-xs text-gray-400 shrink-0">
                        이슈 {item.issue_count}개
                        {item.borderline_count > 0 && ` · 경계 ${item.borderline_count}개`}
                      </span>
                    </div>
                    {item.top_galleries.length > 0 && (
                      <div className="flex items-center gap-3 mt-1 flex-wrap">
                        {item.top_galleries.map(g => (
                          <span key={g.name} className="text-xs text-gray-500">
                            {g.name}{' '}
                            <span className="tabular-nums text-gray-400">{g.score}점</span>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <span className="text-gray-300 group-hover:text-gray-500 text-sm shrink-0 self-center transition-colors">
                    →
                  </span>
                </Link>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
