import Link from 'next/link'
import { getGalleryList } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtDate(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}/${day}`
}

/** 최고 점수 기준 상단 accent 색상 */
function accentColor(maxScore: number, hasRecent: boolean) {
  if (!hasRecent) return { bar: '#e5e7eb', dot: '#9ca3af', text: 'text-gray-400' }
  if (maxScore >= 7)  return { bar: '#ef4444', dot: '#ef4444', text: 'text-red-500' }
  if (maxScore >= 5)  return { bar: '#f97316', dot: '#f97316', text: 'text-orange-500' }
  return { bar: '#f59e0b', dot: '#f59e0b', text: 'text-amber-500' }
}

/** 주 단위 활성 여부를 막대로 표시 */
function WeekBars({ activity }: { activity: [boolean, boolean, boolean, boolean] }) {
  const labels = ['3주전', '2주전', '1주전', '이번주']
  const actReversed = [...activity].reverse() as boolean[] // 왼쪽=오래된 순
  return (
    <div className="flex gap-1 items-end h-6">
      {actReversed.map((active, i) => (
        <div key={i} className="flex flex-col items-center gap-0.5 flex-1">
          <div
            className={`w-full rounded-sm transition-colors ${active ? 'bg-orange-300' : 'bg-gray-100'}`}
            style={{ height: active ? '16px' : '8px' }}
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map(g => {
              const hasRecent = g.recent_issue_days > 0
              const ac = accentColor(g.max_score_4w, hasRecent)

              return (
                <Link
                  key={g.id}
                  href={`/gallery/${g.id}`}
                  className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md hover:border-gray-300 transition-all group flex flex-col"
                >
                  {/* 상단 accent 바 */}
                  <div className="h-1" style={{ backgroundColor: ac.bar }} />

                  <div className="p-4 flex flex-col flex-1 gap-3">
                    {/* 갤러리명 + 심각도 뱃지 */}
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-base font-semibold text-gray-900 leading-snug group-hover:text-gray-700 transition-colors">
                        {g.name}
                      </h3>
                      {hasRecent ? (
                        <span
                          className="text-[11px] font-semibold px-1.5 py-0.5 rounded shrink-0 tabular-nums"
                          style={{ color: ac.dot, backgroundColor: ac.dot + '18' }}
                        >
                          {g.max_score_4w}점
                        </span>
                      ) : (
                        <span className="text-[11px] text-gray-300 shrink-0">이슈 없음</span>
                      )}
                    </div>

                    {/* 4주 활성 막대 */}
                    <div>
                      <p className="text-[10px] text-gray-400 mb-1.5">
                        4주 이슈 현황{' '}
                        {hasRecent && (
                          <span className="text-amber-500 font-medium tabular-nums">
                            {g.recent_issue_days}일
                          </span>
                        )}
                      </p>
                      <WeekBars activity={g.week_activity} />
                    </div>

                    {/* 이슈 빈도 진행 바 */}
                    {hasRecent && (
                      <div>
                        <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all"
                            style={{
                              width: `${Math.min((g.recent_issue_days / 28) * 100, 100)}%`,
                              backgroundColor: ac.bar,
                              opacity: 0.6,
                            }}
                          />
                        </div>
                        <p className="text-[10px] text-gray-300 mt-0.5 tabular-nums text-right">
                          {g.recent_issue_days} / 28일
                        </p>
                      </div>
                    )}

                    {/* 최근 이슈 정보 */}
                    <div className="mt-auto pt-2 border-t border-gray-100 flex items-center justify-between">
                      {g.latest_issue ? (
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 tabular-nums">
                            최근 {fmtDate(g.latest_issue.date)}
                          </span>
                          <span className={`text-xs font-semibold tabular-nums ${
                            g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'
                          }`}>
                            {g.latest_issue.score}점
                          </span>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-300">이슈 기록 없음</span>
                      )}
                      <span className="text-gray-300 group-hover:text-gray-500 text-xs transition-colors">→</span>
                    </div>
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
