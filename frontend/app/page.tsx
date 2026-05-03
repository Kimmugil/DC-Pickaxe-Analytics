import Link from 'next/link'
import type { DailyIssue } from '@/types'
import {
  getCalendarData,
  getLatestWeeklyOverall,
  getRecentIssues,
  getWeeklyListWithInfo,
} from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { CalendarClient } from '@/components/CalendarClient'
import { IssueCardFull } from '@/components/IssueCardFull'

function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

function fmtMonth(d: string) {
  if (!d) return ''
  const [y, m] = d.split('-').map(Number)
  return `${y}년 ${m}월`
}

// ── 직전 월 요약 ────────────────────────────────────────────────────
function MonthlySection({
  weeklyList,
  t,
}: {
  weeklyList: Awaited<ReturnType<typeof getWeeklyListWithInfo>>
  t: Record<string, string>
}) {
  if (!weeklyList.length) return null

  // 가장 최근 달 기준
  const latestMonth = weeklyList[0].week_start.slice(0, 7) // 'YYYY-MM'
  const thisMonthWeeks = weeklyList.filter(w => w.week_start.slice(0, 7) === latestMonth)
  if (!thisMonthWeeks.length) return null

  const [y, m] = latestMonth.split('-').map(Number)

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            {t['home.monthly_summary.title'] ?? `${y}년 ${m}월 요약`}
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {tp(t, 'home.monthly_summary.week_count', { count: thisMonthWeeks.length }, '{count}주')}
          </p>
        </div>
        <Link href="/reports" className="text-xs text-gray-400 hover:text-gray-700 transition-colors">
          {t['common.view_all'] ?? '전체 보기 →'}
        </Link>
      </div>
      <div className="space-y-2">
        {thisMonthWeeks.map(w => (
          <Link
            key={w.week_start}
            href={`/weekly/${w.week_start}`}
            className="block bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors"
          >
            <div className="flex items-center justify-between gap-2 mb-1">
              <span className="text-xs font-semibold text-gray-700">
                {fmtShort(w.week_start)} ~ {fmtShort(w.week_end)}
              </span>
              <span className="text-[11px] text-gray-400 tabular-nums shrink-0">
                {tp(t, 'common.gallery_count', { count: w.gallery_count }, '{count}개')}
              </span>
            </div>
            {w.ai_summary ? (
              <p className="text-xs text-gray-500 leading-relaxed line-clamp-2">{w.ai_summary}</p>
            ) : (
              <p className="text-xs text-gray-300">{t['common.no_summary'] ?? '요약 없음'}</p>
            )}
          </Link>
        ))}
      </div>
    </section>
  )
}

// ── 직전 주 요약 ─────────────────────────────────────────────────────
function WeeklySummarySection({
  data,
  t,
}: {
  data: Awaited<ReturnType<typeof getLatestWeeklyOverall>>
  t: Record<string, string>
}) {
  if (!data) return null

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            {t['home.weekly_summary.title'] ?? '직전 주 종합 요약'}
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {fmtShort(data.week_start)} ~ {fmtShort(data.week_end)}
          </p>
        </div>
        <Link href={`/weekly/${data.week_start}`} className="text-xs text-gray-400 hover:text-gray-700 transition-colors">
          {t['common.view_all'] ?? '전체 보기 →'}
        </Link>
      </div>

      {data.ai_summary && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{data.ai_summary}</p>
        </div>
      )}
    </section>
  )
}

// ── 홈 페이지 ─────────────────────────────────────────────────────────────

export default async function HomePage() {
  const [t, cal, recentIssues, weeklySummary, weeklyList] = await Promise.all([
    getTexts(),
    getCalendarData().catch(() => ({
      issuesByDate: {} as Record<string, { id: string; name: string; score: number; cause?: string }[]>,
      weeklyDates: [] as string[],
    })),
    getRecentIssues(3).catch(() => [] as DailyIssue[]),
    getLatestWeeklyOverall().catch(() => null),
    getWeeklyListWithInfo().catch(() => []),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="home" />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">

        {/* ① 이슈 캘린더 */}
        <section className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-xs font-medium text-gray-400">
              {t['home.calendar.title'] ?? '이슈 캘린더'}
            </h2>
            <Link href="/daily" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
              {t['common.view_all'] ?? '전체 보기 →'}
            </Link>
          </div>
          <CalendarClient issuesByDate={cal.issuesByDate} weeklyDates={cal.weeklyDates} />
        </section>

        {/* ② 최근 이슈 카드 */}
        {recentIssues.length > 0 && (
          <section className="space-y-3">
            <div className="flex items-baseline justify-between">
              <h2 className="text-sm font-semibold text-gray-900">
                {t['home.recent_issues.title'] ?? '최근 이슈'}
              </h2>
              <Link href="/daily" className="text-xs text-gray-400 hover:text-gray-700 transition-colors">
                {t['common.view_all'] ?? '전체 보기 →'}
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {recentIssues.map(issue => (
                <IssueCardFull
                  key={`${issue.date}-${issue.gallery_id}`}
                  issue={issue}
                  t={t}
                  headerLeft={
                    <div className="flex items-center gap-2 flex-wrap">
                      <Link href={`/gallery/${issue.gallery_id}`} className="text-sm font-semibold text-gray-900 hover:underline">
                        {issue.gallery_name}
                      </Link>
                      <span className="text-xs text-gray-400 tabular-nums">
                        {issue.date.slice(5).replace('-', '/')}
                      </span>
                    </div>
                  }
                />
              ))}
            </div>
          </section>
        )}

        {/* ③ 직전 주 종합 요약 */}
        <WeeklySummarySection data={weeklySummary} t={t} />

        {/* ④ 직전 월 요약 */}
        <MonthlySection weeklyList={weeklyList} t={t} />

      </main>
    </div>
  )
}
