import Link from 'next/link'
import type { DailyIssue } from '@/types'
import { getCalendarData, getRecentIssues } from '@/lib/data'
import { getTexts } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { CalendarClient } from '@/components/CalendarClient'
import { IssueCardFull } from '@/components/IssueCardFull'

export default async function HomePage() {
  const [t, cal, recentIssues] = await Promise.all([
    getTexts(),
    getCalendarData().catch(() => ({
      issuesByDate: {} as Record<string, { id: string; name: string; score: number; cause?: string }[]>,
      weeklyDates: [] as string[],
    })),
    getRecentIssues(3).catch(() => [] as DailyIssue[]),
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
          <CalendarClient issuesByDate={cal.issuesByDate} weeklyDates={cal.weeklyDates} t={t} />
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
            <div className="space-y-3">
              {recentIssues.map(issue => (
                <IssueCardFull
                  key={`${issue.date}-${issue.gallery_id}`}
                  issue={issue}
                  t={t}
                  collapsible={true}
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

      </main>
    </div>
  )
}
