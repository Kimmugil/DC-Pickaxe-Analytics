import Link from 'next/link'
import { getGalleryList } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtDate(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}/${day}`
}

export default async function GalleryListPage() {
  const [t, list] = await Promise.all([
    getTexts(),
    getGalleryList().catch(() => [] as Awaited<ReturnType<typeof getGalleryList>>),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="gallery" />

      <main className="max-w-4xl mx-auto px-4 py-6">
        <p className="text-xs text-gray-400 mb-4">
          {tp(t, 'gallery_list.description', { count: list.length }, '모니터링 중인 갤러리 {count}개 · 최근 4주 이슈 횟수 기준 정렬')}
        </p>

        {list.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="space-y-1.5">
            {list.map(g => (
              <Link
                key={g.id}
                href={`/gallery/${g.id}`}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="text-sm font-medium text-gray-900 truncate">{g.name}</span>
                  {g.recent_issue_days > 0 && (
                    <span className="text-xs text-amber-600 tabular-nums shrink-0">
                      {tp(t, 'gallery_list.recent_issue_days', { count: g.recent_issue_days }, '최근 4주 {count}일 이슈')}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-3">
                  {g.latest_issue ? (
                    <span className="text-xs text-gray-400 tabular-nums">
                      {fmtDate(g.latest_issue.date)}{' '}
                      <span className={g.latest_issue.score >= 7 ? 'text-red-500 font-medium' : 'text-orange-500 font-medium'}>
                        {g.latest_issue.score}점
                      </span>
                    </span>
                  ) : (
                    <span className="text-xs text-gray-300">이슈 없음</span>
                  )}
                  <span className="text-gray-300 group-hover:text-gray-500 text-sm transition-colors">→</span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
