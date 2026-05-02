import type { TimelineItem } from '@/lib/data'
import { getAllTimeline } from '@/lib/data'
import { getTexts } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { TimelineAccordion } from '@/components/TimelineAccordion'

export default async function TimelinePage() {
  const [t, timeline] = await Promise.all([
    getTexts(),
    getAllTimeline(120).catch(() => [] as TimelineItem[]),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="timeline" />

      <main className="max-w-3xl mx-auto px-4 py-6">
        {timeline.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <TimelineAccordion items={timeline} t={t} />
        )}
      </main>
    </div>
  )
}
