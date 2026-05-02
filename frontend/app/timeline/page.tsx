import Link from 'next/link'
import type { TimelineItem } from '@/lib/data'
import { getAllTimeline } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { galleryColor } from '@/lib/galleryColors'

function fmtDate(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}
function fmtWeek(s: string, e: string) {
  if (!s) return ''
  const [, sm, sd] = s.split('-').map(Number)
  const [, em, ed] = (e || s).split('-').map(Number)
  return `${sm}/${sd} ~ ${em}/${ed}`
}

function IssueTimelineCard({ item, t }: { item: Extract<TimelineItem, { kind: 'issue' }>; t: Record<string, string> }) {
  const isHigh = item.max_score >= 7
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center shrink-0">
        <div className={`w-3 h-3 rounded-full mt-1.5 shrink-0 ${isHigh ? 'bg-red-500' : 'bg-orange-400'}`} />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 flex-1">
        <div className="flex items-center justify-between mb-3 gap-2 flex-wrap">
          <Link href={`/daily/${item.date}`} className="text-sm font-semibold text-gray-900 hover:underline">
            {fmtDate(item.date)}
          </Link>
          <span className={`text-xs font-medium tabular-nums ${isHigh ? 'text-red-600' : 'text-orange-500'}`}>
            {tp(t, 'common.issue_count', { count: item.issue_count }, '이슈 {count}개')}
          </span>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {item.galleries.map(g => {
            const c = galleryColor(g.id)
            return (
              <Link
                key={g.id}
                href={`/gallery/${g.id}`}
                className={`flex items-center gap-1 ${c.bg} ${c.text} text-xs font-medium px-2 py-0.5 rounded hover:opacity-80 transition-opacity`}
              >
                {g.name}
                <span className="text-gray-500 tabular-nums font-normal">{g.score}점</span>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function WeeklyTimelineCard({ item, t }: { item: Extract<TimelineItem, { kind: 'weekly' }>; t: Record<string, string> }) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center shrink-0">
        <div className="w-3 h-3 rounded-full mt-1.5 bg-blue-300 shrink-0" />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <Link
        href={`/weekly/${item.week_start}`}
        className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4 flex-1 hover:border-blue-200 transition-colors block"
      >
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-sm font-semibold text-blue-800">
            {t['gallery_detail.weekly_badge'] ?? '주간'} {fmtWeek(item.week_start, item.week_end)}
          </span>
          <span className="text-xs text-blue-400 tabular-nums shrink-0">
            {tp(t, 'common.gallery_count', { count: item.gallery_count }, '{count}개 갤러리')}
          </span>
        </div>
        {item.ai_summary && (
          <p className="text-sm text-blue-700 leading-relaxed line-clamp-2">{item.ai_summary}</p>
        )}
      </Link>
    </div>
  )
}

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
          <div>
            {timeline.map(item =>
              item.kind === 'issue'
                ? <IssueTimelineCard key={`i-${item.date}`} item={item} t={t} />
                : <WeeklyTimelineCard key={`w-${item.date}`} item={item} t={t} />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
