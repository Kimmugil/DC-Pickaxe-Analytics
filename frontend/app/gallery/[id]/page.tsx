import type { DailyIssue, WeeklyGallery } from '@/types'
import { notFound } from 'next/navigation'
import { getGalleryHistory } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { GalleryTimelineClient } from '@/components/GalleryTimelineClient'

interface Props { params: Promise<{ id: string }> }

type TimelineEntry =
  | { kind: 'issue';  sortKey: string; data: DailyIssue }
  | { kind: 'weekly'; sortKey: string; data: WeeklyGallery }

export default async function GalleryDetailPage({ params }: Props) {
  const { id } = await params

  const [t, history] = await Promise.all([
    getTexts(),
    getGalleryHistory(id).catch(() => null),
  ])

  if (!history) notFound()

  const { gallery_name, issues, weeklies } = history

  const timeline: TimelineEntry[] = [
    ...issues.map(i => ({ kind: 'issue'  as const, sortKey: i.date,       data: i })),
    ...weeklies.map(w => ({ kind: 'weekly' as const, sortKey: w.week_start, data: w })),
  ].sort((a, b) => b.sortKey.localeCompare(a.sortKey))

  const recentIssueDays = issues.filter(i => i.has_issue).length

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav back={{ href: '/gallery', label: t['nav.gallery'] ?? '갤러리' }} title={gallery_name} />

      <main className="max-w-3xl mx-auto px-4 py-6">
        {recentIssueDays > 0 && (
          <p className="text-xs text-amber-600 mb-4">
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
