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

const CAUSE_STYLE: Record<string, string> = {
  컨텐츠: 'text-blue-600 bg-blue-50',
  운영:   'text-orange-600 bg-orange-50',
  화제:   'text-purple-600 bg-purple-50',
}

function IssueCard({ issue, t }: { issue: DailyIssue; t: Record<string, string> }) {
  const kws  = Array.isArray(issue.keywords)  ? issue.keywords  : []
  const tops = Array.isArray(issue.top_posts) ? issue.top_posts : []
  const isHigh = issue.issue_score >= 7
  const base = Math.max(issue.avg_same_weekday ?? 0, issue.avg_7d)
  const pct  = base > 0 ? ((issue.posts_total - base) / base) * 100 : 0

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      {/* 날짜 + 갤러리명 + 점수 */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <Link href={`/gallery/${issue.gallery_id}`} className="text-sm font-semibold text-gray-900 hover:underline">
            {issue.gallery_name}
          </Link>
          <span className={`text-xs font-semibold tabular-nums ${isHigh ? 'text-red-600' : issue.has_issue ? 'text-orange-500' : 'text-amber-500'}`}>
            {issue.issue_score}점
          </span>
          {!issue.has_issue && issue.is_borderline && (
            <span className="text-xs text-gray-400">{t['common.borderline_label'] ?? '경계'}</span>
          )}
          {issue.temperature_tag && (
            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">{issue.temperature_tag}</span>
          )}
          {issue.issue_cause && issue.issue_cause !== '기타' && (
            <span className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${CAUSE_STYLE[issue.issue_cause] ?? 'text-gray-500 bg-gray-100'}`}>
              {issue.issue_cause}
            </span>
          )}
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

      {/* 날짜 (secondary) */}
      <Link href={`/daily/${issue.date}`} className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
        {fmtDate(issue.date)} →
      </Link>

      {issue.ai_summary && (
        <p className="text-sm text-gray-600 leading-relaxed">{issue.ai_summary}</p>
      )}

      {kws.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {kws.slice(0, 6).map(([kw, cnt]) => (
            <span key={kw} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
              #{kw} <span className="text-gray-400 tabular-nums">{cnt}</span>
            </span>
          ))}
        </div>
      )}

      {tops.length > 0 && (
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="daily" />

      <main className="max-w-5xl mx-auto px-4 py-6">
        {feed.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {feed.map(issue => (
              <IssueCard
                key={`${issue.date}-${issue.gallery_id}`}
                issue={issue}
                t={t}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
