import Link from 'next/link'
import type { DailyIssue } from '@/types'
import {
  getCalendarData,
  getLatestWeeklyOverall,
  getRecentIssues,
  getLatestMonthlyOverall,
} from '@/lib/data'
import { getTexts } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { CalendarClient } from '@/components/CalendarClient'
import { IssueCardFull } from '@/components/IssueCardFull'

function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

// ── 직전 월 요약 ────────────────────────────────────────────────────
function MonthlySection({
  monthly,
  t,
}: {
  monthly: Awaited<ReturnType<typeof getLatestMonthlyOverall>>
  t: Record<string, string>
}) {
  if (!monthly?.ai_summary) return null

  const [y, m] = monthly.month.split('-').map(Number)

  return (
    <section className="space-y-3">
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            {t['home.monthly_summary.title'] ?? `${y}년 ${m}월 요약`}
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">{`${y}년 ${m}월`}</p>
        </div>
        <Link href="/reports" className="text-xs text-gray-400 hover:text-gray-700 transition-colors">
          {t['common.view_all'] ?? '전체 보기 →'}
        </Link>
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{monthly.ai_summary}</p>
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
  const [t, cal, recentIssues, weeklySummary, monthlySummary] = await Promise.all([
    getTexts(),
    getCalendarData().catch(() => ({
      issuesByDate: {} as Record<string, { id: string; name: string; score: number; cause?: string }[]>,
      weeklyDates: [] as string[],
    })),
    getRecentIssues(3).catch(() => [] as DailyIssue[]),
    getLatestWeeklyOverall().catch(() => null),
    getLatestMonthlyOverall().catch(() => null),
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
        <MonthlySection monthly={monthlySummary} t={t} />

      </main>
    </div>
  )
}
