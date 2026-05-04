import type { DailyIssue, WeeklyGallery, MonthlyGallery } from '@/types'
import { notFound } from 'next/navigation'
import { getGalleryHistory, getGalleryCalendarData } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { CalendarClient } from '@/components/CalendarClient'
import { GalleryTimelineClient } from '@/components/GalleryTimelineClient'

interface Props { params: Promise<{ id: string }> }

type TimelineEntry =
  | { kind: 'issue';   sortKey: string; data: DailyIssue }
  | { kind: 'weekly';  sortKey: string; data: WeeklyGallery }
  | { kind: 'monthly'; sortKey: string; data: MonthlyGallery }

export default async function GalleryDetailPage({ params }: Props) {
  const { id } = await params

  const [t, history, calData] = await Promise.all([
    getTexts(),
    getGalleryHistory(id).catch(() => null),
    getGalleryCalendarData(id).catch(() => ({
      issuesByDate: {} as Record<string, { id: string; name: string; score: number; cause?: string }[]>,
      weeklyDates: [] as string[],
    })),
  ])

  if (!history) notFound()

  const { gallery_name, issues, weeklies, monthlies } = history

  // 월간 리포트는 해당 월의 마지막에 표시 (sortKey: month + '-31')
  const timeline: TimelineEntry[] = [
    ...issues.map(i => ({ kind: 'issue'   as const, sortKey: i.date,              data: i })),
    ...weeklies.map(w => ({ kind: 'weekly'  as const, sortKey: w.week_start,        data: w })),
    ...monthlies.map(m => ({ kind: 'monthly' as const, sortKey: m.month + '-31',     data: m })),
  ].sort((a, b) => b.sortKey.localeCompare(a.sortKey))

  const recentIssueDays = issues.filter(i => i.has_issue).length

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav
        back={{ href: '/gallery', label: t['nav.gallery'] ?? '갤러리별 리포트' }}
        title={gallery_name}
        active="gallery"
      />

      <main className="max-w-3xl mx-auto px-4 py-6 space-y-6">

        {/* 갤러리별 이슈 캘린더 */}
        <section className="bg-white border border-gray-200 rounded-lg p-4">
          <h2 className="text-xs font-medium text-gray-400 mb-3">
            {t['gallery_detail.calendar_title'] ?? '이슈 캘린더'}
          </h2>
          <CalendarClient
            issuesByDate={calData.issuesByDate}
            weeklyDates={calData.weeklyDates}
            t={t}
            galleryId={id}
          />
        </section>

        {recentIssueDays > 0 && (
          <p className="text-xs text-amber-600">
            {tp(t, 'gallery_detail.total_issues', { count: recentIssueDays }, '총 {count}회 이슈 기록')}
          </p>
        )}

        {timeline.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['gallery_detail.no_history'] ?? '기록 없음'}
          </p>
        ) : (
          <GalleryTimelineClient timeline={timeline} t={t} />
        )}
      </main>
    </div>
  )
}
