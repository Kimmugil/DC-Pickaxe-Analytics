import Link from 'next/link'
import type { DailyIssue } from '@/types'
import { getIssueFeed } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtDate(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

const CAUSE_STYLE: Record<string, { bg: string; text: string }> = {
  컨텐츠: { bg: '#eff6ff', text: '#1d4ed8' },
  운영:   { bg: '#fff7ed', text: '#c2410c' },
  밸런스: { bg: '#fef9c3', text: '#854d0e' },
  버그:   { bg: '#fee2e2', text: '#991b1b' },
  결제:   { bg: '#fdf4ff', text: '#7e22ce' },
  화제:   { bg: '#f0fdf4', text: '#166534' },
}

const CATEGORY_LABEL: Record<string, string> = {
  balance: '밸런스', operation: '운영', bug: '버그', payment: '결제', content: '컨텐츠',
}
const CAUSE_LABEL: Record<string, string> = { ...CATEGORY_LABEL }

function CategoryBar({ scores }: { scores: DailyIssue['category_scores'] }) {
  if (!scores) return null
  const entries = Object.entries(scores) as [string, { score: number; summary: string }][]
  const hasAny = entries.some(([, v]) => v.score > 0)
  if (!hasAny) return null
  return (
    <div className="space-y-1">
      {entries.filter(([, v]) => v.score > 0).map(([k, v]) => (
        <div key={k} className="flex items-center gap-2 text-xs">
          <span className="text-gray-400 w-10 shrink-0">{CATEGORY_LABEL[k] ?? k}</span>
          <div className="flex gap-0.5">
            {[1, 2, 3].map(i => (
              <div key={i} className="w-3 h-2 rounded-sm"
                style={{ backgroundColor: i <= v.score ? '#f97316' : '#e5e7eb' }} />
            ))}
          </div>
          {v.summary && <span className="text-gray-500 line-clamp-1 flex-1">{v.summary}</span>}
        </div>
      ))}
    </div>
  )
}

function IssueCard({ issue, t }: { issue: DailyIssue; t: Record<string, string> }) {
  const kws  = Array.isArray(issue.keywords)  ? issue.keywords  : []
  const tops = Array.isArray(issue.top_posts) ? issue.top_posts : []
  const majors = Array.isArray(issue.major_issues) ? issue.major_issues : []
  const isHigh = issue.issue_score >= 7
  const base = Math.max(issue.avg_same_weekday ?? 0, issue.avg_7d)
  const pct  = base > 0 ? ((issue.posts_total - base) / base) * 100 : 0

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <Link href={`/gallery/${issue.gallery_id}`} className="text-sm font-semibold text-gray-900 hover:underline">
            {issue.gallery_name}
          </Link>
          <span className={`text-xs font-bold tabular-nums ${isHigh ? 'text-red-600' : issue.has_issue ? 'text-orange-500' : 'text-amber-500'}`}>
            {issue.issue_score}점
          </span>
          {!issue.has_issue && issue.is_borderline && (
            <span className="text-xs text-gray-400">{t['common.borderline_label'] ?? '경계'}</span>
          )}
          {issue.temperature_tag && (
            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">{issue.temperature_tag}</span>
          )}
          {issue.issue_cause && issue.issue_cause !== '기타' && (() => {
            const label = CAUSE_LABEL[issue.issue_cause!] ?? issue.issue_cause!
            const s = CAUSE_STYLE[label] ?? { bg: '#f9fafb', text: '#6b7280' }
            return (
              <span className="text-[11px] font-medium px-1.5 py-0.5 rounded" style={{ backgroundColor: s.bg, color: s.text }}>
                {label}
              </span>
            )
          })()}
        </div>
        <div className="text-right text-xs text-gray-500 shrink-0">
          <span className="font-semibold text-gray-700 tabular-nums">{issue.posts_total}건</span>
          <span className="text-gray-400 ml-1 tabular-nums">
            {tp(t, 'daily_detail.avg_7d', { count: issue.avg_7d }, '7일평균 {count}건')}
            {pct !== 0 && (
              <span className={pct > 0 ? ' text-red-500' : ' text-green-500'}>
                {' '}({pct > 0 ? '+' : ''}{pct.toFixed(0)}%)
              </span>
            )}
          </span>
        </div>
      </div>

      {/* 헤드라인 */}
      {issue.headline && (
        <p className="text-sm font-semibold text-gray-800">{issue.headline}</p>
      )}

      {/* AI 요약 */}
      {issue.ai_summary && (
        <p className="text-sm text-gray-600 leading-relaxed">{issue.ai_summary}</p>
      )}

      {/* 카테고리 점수 */}
      <CategoryBar scores={issue.category_scores} />

      {/* 주요 이슈 */}
      {majors.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-gray-100">
          {majors.slice(0, 3).map((m, i) => (
            <div key={i} className="text-xs space-y-0.5">
              <div className="flex items-center gap-1.5">
                <span className="font-semibold text-gray-700">{m.title}</span>
                {m.mention_count > 0 && (
                  <span className="text-gray-400 tabular-nums">언급 {m.mention_count}건</span>
                )}
                {m.ref_url && (
                  <a href={m.ref_url} target="_blank" rel="noopener noreferrer"
                    className="text-blue-400 hover:underline">↗</a>
                )}
              </div>
              {m.detail && <p className="text-gray-500 leading-relaxed">{m.detail}</p>}
            </div>
          ))}
        </div>
      )}

      {/* 감정 분위기 */}
      {(issue.sentiment?.positive || issue.sentiment?.negative) && (
        <div className="flex flex-col gap-1 pt-1 border-t border-gray-100 text-xs">
          {issue.sentiment.positive && (
            <p className="text-green-700"><span className="font-medium">긍정</span> {issue.sentiment.positive}</p>
          )}
          {issue.sentiment.negative && (
            <p className="text-red-600"><span className="font-medium">부정</span> {issue.sentiment.negative}</p>
          )}
        </div>
      )}

      {/* 키워드 */}
      {kws.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {kws.slice(0, 6).map(([kw, cnt]) => (
            <span key={kw} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
              #{kw} <span className="text-gray-400 tabular-nums">{cnt}</span>
            </span>
          ))}
        </div>
      )}

      {/* 상위 게시글 (major_issues가 없을 때만 표시) */}
      {majors.length === 0 && tops.length > 0 && (
        <div className="space-y-1 pt-2 border-t border-gray-100">
          {tops.slice(0, 3).map((p, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="text-gray-300 w-3 tabular-nums shrink-0">{i + 1}</span>
              <a href={p.링크} target="_blank" rel="noopener noreferrer"
                className="text-gray-700 hover:underline line-clamp-1 flex-1">
                {p.제목}
              </a>
              <span className="text-gray-400 tabular-nums shrink-0">댓글 {p.댓글수}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

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
  const dateGroups = Array.from(byDate.entries()).sort((a, b) => b[0].localeCompare(a[0]))

  const c1 = t['daily.criteria.line1'] ?? '① 게시량 급증 0~4점 — 기준선 대비 1.5배 이상 증가 (기준선 = 동요일 4주 평균 우선, 없으면 7일 단순 평균)'
  const c2 = t['daily.criteria.line2'] ?? '② 게시글 화제성 0~3점 — 소규모: 최다 댓글 5/12/25개↑, 중규모: 10/20/35개↑, 대규모: 15/30/50개↑'
  const c3 = t['daily.criteria.line3'] ?? '③ 바이럴 확산 0~3점 — 소규모: 댓글5개↑ 게시글 1/2/3개, 중규모: 댓글8개↑ 2/3/4개, 대규모: 댓글10개↑ 2/3/5개'
  const c4 = t['daily.criteria.line4'] ?? '④ 모멘텀 보너스 0~1점 — 직전 3일 이동평균도 기준선 대비 30% 이상 상승 중'
  const c5 = t['daily.criteria.line5'] ?? '※ 규모 기준: 소규모 = 일평균 30건 미만, 중규모 = 30~100건, 대규모 = 100건 이상'
  const cTh = t['daily.criteria.threshold'] ?? '5점 이상 = 이슈 발행 · 4점 = 경계(주목) · 7점 이상 = 고위험'

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="daily" />

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
            <p className="text-xs text-gray-500 pt-1 border-t border-gray-100 mt-2">
              {cTh}
            </p>
          </div>
        </details>

        {dateGroups.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="space-y-6">
            {dateGroups.map(([date, issues]) => (
              <section key={date}>
                {/* 날짜 구분선 */}
                <div className="flex items-center gap-3 mb-3">
                  <Link href={`/daily/${date}`} className="text-sm font-semibold text-gray-600 hover:text-gray-900 transition-colors whitespace-nowrap">
                    {fmtDate(date)}
                  </Link>
                  <div className="flex-1 h-px bg-gray-200" />
                  <span className="text-xs text-gray-400 tabular-nums shrink-0">
                    {tp(t, 'common.issue_count', { count: issues.filter(i => i.has_issue).length }, '이슈 {count}개')}
                  </span>
                </div>

                {/* 갤러리 카드 */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {issues.map(issue => (
                    <IssueCard key={`${issue.date}-${issue.gallery_id}`} issue={issue} t={t} />
                  ))}
                </div>
              </section>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
