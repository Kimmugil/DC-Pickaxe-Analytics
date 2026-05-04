import type { DailyIssue } from '@/types'
import { getIssueFeed } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { DailyFilterGrid } from '@/components/DailyFilterGrid'

export default async function DailyListPage() {
  const [t, feed] = await Promise.all([
    getTexts(),
    getIssueFeed(80).catch(() => [] as DailyIssue[]),
  ])

  // 날짜별 그룹
  const byDate = new Map<string, DailyIssue[]>()
  for (const issue of feed) {
    if (!byDate.has(issue.date)) byDate.set(issue.date, [])
    byDate.get(issue.date)!.push(issue)
  }
  const dateGroups = Array.from(byDate.entries())
    .sort((a, b) => b[0].localeCompare(a[0]))
    .map(([date, issues]) => ({ date, issues }))

  // 갤러리 목록 (필터용)
  const galleryMap = new Map<string, string>()
  for (const issue of feed) {
    if (!galleryMap.has(issue.gallery_id)) galleryMap.set(issue.gallery_id, issue.gallery_name)
  }
  const galleries = Array.from(galleryMap.entries())
    .map(([id, name]) => ({ id, name }))
    .sort((a, b) => a.name.localeCompare(b.name))

  const c1 = t['daily.criteria.line1'] ?? '① 게시량 급증 0~4점 — 기준선 대비 1.5배 이상 증가 (기준선 = 동요일 4주 평균 우선, 없으면 7일 단순 평균)'
  const c2 = t['daily.criteria.line2'] ?? '② 게시글 화제성 0~3점 — 소규모: 최다 댓글 5/12/25개↑, 중규모: 10/20/35개↑, 대규모: 15/30/50개↑'
  const c3 = t['daily.criteria.line3'] ?? '③ 바이럴 확산 0~3점 — 소규모: 댓글5개↑ 게시글 1/2/3개, 중규모: 댓글8개↑ 2/3/4개, 대규모: 댓글10개↑ 2/3/5개'
  const c4 = t['daily.criteria.line4'] ?? '④ 모멘텀 보너스 0~1점 — 직전 3일 이동평균도 기준선 대비 30% 이상 상승 중'
  const c5 = t['daily.criteria.line5'] ?? '※ 규모 기준: 소규모 = 일평균 30건 미만, 중규모 = 30~100건, 대규모 = 100건 이상'
  const cTh = t['daily.criteria.threshold'] ?? '5점 이상 = 이슈 발행 · 4점 = 경계(주목) · 7점 이상 = 고위험'

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="timeline" />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-4">

        {/* 이슈 판정 기준 메모 */}
        <details className="group bg-white border border-gray-200 rounded-lg overflow-hidden">
          <summary className="flex items-center justify-between px-4 py-3 cursor-pointer select-none list-none hover:bg-gray-50 transition-colors">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-gray-600">
                {t['daily.criteria.title'] ?? '이슈 판정 기준'}
              </span>
              <span className="text-[11px] text-gray-400">{cTh}</span>
            </div>
            <span className="text-gray-400 text-xs group-open:rotate-180 transition-transform">▾</span>
          </summary>
          <div className="px-4 pb-4 pt-1 space-y-1.5 border-t border-gray-100">
            {[c1, c2, c3, c4].map((line, i) => (
              <p key={i} className="text-xs text-gray-600 leading-relaxed">{line}</p>
            ))}
            <p className="text-xs text-gray-400 leading-relaxed">{c5}</p>
            <p className="text-xs text-gray-500 pt-1 border-t border-gray-100 mt-2">{cTh}</p>
          </div>
        </details>

        {dateGroups.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <DailyFilterGrid dateGroups={dateGroups} galleries={galleries} t={t} />
        )}
      </main>
    </div>
  )
}
