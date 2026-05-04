import Link from 'next/link'
import { getGalleryList } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtDate(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}/${day}`
}

function ScoreBadge({ score }: { score: number }) {
  if (score >= 7) return (
    <span className="inline-flex items-center gap-1 text-xs font-bold text-red-600 bg-red-50 border border-red-200 rounded-full px-2.5 py-0.5 tabular-nums">
      <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block" />
      {score}점
    </span>
  )
  if (score >= 5) return (
    <span className="inline-flex items-center gap-1 text-xs font-bold text-orange-600 bg-orange-50 border border-orange-200 rounded-full px-2.5 py-0.5 tabular-nums">
      <span className="w-1.5 h-1.5 rounded-full bg-orange-400 inline-block" />
      {score}점
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 text-xs font-bold text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2.5 py-0.5 tabular-nums">
      <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block" />
      {score}점
    </span>
  )
}

/** 주 단위 활성 여부를 막대로 표시 */
function WeekBars({ activity }: { activity: [boolean, boolean, boolean, boolean] }) {
  const labels = ['3주전', '2주전', '1주전', '이번주']
  const actReversed = [...activity].reverse() as boolean[]
  return (
    <div className="flex gap-1 items-end h-5">
      {actReversed.map((active, i) => (
        <div key={i} className="flex flex-col items-center gap-0.5 flex-1">
          <div
            className={`w-full rounded-sm ${active ? 'bg-orange-300' : 'bg-gray-100'}`}
            style={{ height: active ? '14px' : '6px' }}
          />
          <span className="text-[7px] text-gray-300 leading-none">{labels[i]}</span>
        </div>
      ))}
    </div>
  )
}

export default async function GalleryListPage() {
  const [t, list] = await Promise.all([
    getTexts(),
    getGalleryList().catch(() => [] as Awaited<ReturnType<typeof getGalleryList>>),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="gallery" />

      <main className="max-w-5xl mx-auto px-4 py-6">
        <p className="text-xs text-gray-400 mb-5">
          {tp(t, 'gallery_list.description', { count: list.length }, '모니터링 중인 갤러리 {count}개 · 최근 4주 이슈 횟수 기준 정렬')}
        </p>

        {list.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {list.map(g => {
              const hasRecent = g.recent_issue_days > 0

              return (
                <Link
                  key={g.id}
                  href={`/gallery/${g.id}`}
                  className="bg-white border border-gray-200 rounded-xl hover:shadow-sm hover:border-gray-300 transition-all group flex flex-col p-4 gap-3"
                >
                  {/* 갤러리명 + 심각도 뱃지 */}
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="text-sm font-semibold text-gray-900 leading-snug group-hover:text-gray-700 transition-colors">
                      {g.name}
                    </h3>
                    {hasRecent
                      ? <ScoreBadge score={g.max_score_4w} />
                      : <span className="text-[11px] text-gray-300 shrink-0 pt-0.5">이슈 없음</span>
                    }
                  </div>

                  {/* 4주 활성 막대 */}
                  <div>
                    <p className="text-[10px] text-gray-400 mb-1.5">
                      최근 4주
                      {hasRecent && (
                        <span className="ml-1 text-gray-500 font-medium tabular-nums">
                          {g.recent_issue_days}일 이슈
                        </span>
                      )}
                    </p>
                    <WeekBars activity={g.week_activity} />
                  </div>

                  {/* 최근 이슈 */}
                  <div className="pt-2 border-t border-gray-100 flex items-center justify-between mt-auto">
                    {g.latest_issue ? (
                      <span className="text-xs text-gray-400 tabular-nums">
                        최근 {fmtDate(g.latest_issue.date)}{' '}
                        <span className={`font-semibold ${
                          g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'
                        }`}>
                          {g.latest_issue.score}점
                        </span>
                      </span>
                    ) : (
                      <span className="text-xs text-gray-300">이슈 기록 없음</span>
                    )}
                    <span className="text-gray-300 group-hover:text-gray-500 text-xs transition-colors">→</span>
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
