import Link from 'next/link'
import { getWeeklyListWithInfo } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmt(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

export default async function WeeklyListPage() {
  const [t, list] = await Promise.all([
    getTexts(),
    getWeeklyListWithInfo().catch(() => [] as Awaited<ReturnType<typeof getWeeklyListWithInfo>>),
  ])

  const title = t['weekly_list.title'] ?? '주간 리포트 목록'

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav back={{ href: '/reports' }} title={title} />

      <main className="max-w-4xl mx-auto px-4 py-6">
        {list.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="space-y-1.5">
            {list.map(item => (
              <Link
                key={item.week_start}
                href={`/weekly/${item.week_start}`}
                className="flex items-start justify-between bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-900">
                      {fmt(item.week_start)} ~ {fmt(item.week_end)}
                    </span>
                    <span className="text-xs text-gray-400">
                      {tp(t, 'common.gallery_count', { count: item.gallery_count }, '{count}개 갤러리')}
                    </span>
                  </div>
                  {item.ai_summary && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-1">{item.ai_summary}</p>
                  )}
                </div>
                <span className="text-gray-300 group-hover:text-gray-500 text-sm ml-3 shrink-0 self-center transition-colors">→</span>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
