import Link from 'next/link'
import type { DailyIssue, WeeklyGallery } from '@/types'
import { notFound } from 'next/navigation'
import { getGalleryHistory } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'

interface Props { params: Promise<{ id: string }> }

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

const CAUSE_STYLE: Record<string, string> = {
  컨텐츠: 'text-blue-600 bg-blue-50',
  운영:   'text-orange-600 bg-orange-50',
  화제:   'text-purple-600 bg-purple-50',
}

// ── 타임라인 엔트리 유형 ──────────────────────────────────────────────────

type TimelineEntry =
  | { kind: 'issue';  sortKey: string; data: DailyIssue }
  | { kind: 'weekly'; sortKey: string; data: WeeklyGallery }

function IssueEntry({ issue, t }: { issue: DailyIssue; t: Record<string, string> }) {
  const kws  = Array.isArray(issue.keywords)  ? issue.keywords  : []
  const tops = Array.isArray(issue.top_posts) ? issue.top_posts : []
  const isHigh = issue.issue_score >= 7

  return (
    <div id={`issue-${issue.date}`} className="flex gap-4">
      {/* 타임라인 인디케이터 */}
      <div className="flex flex-col items-center shrink-0">
        <div className={`w-3 h-3 rounded-full mt-1 ${isHigh ? 'bg-red-500' : issue.has_issue ? 'bg-orange-400' : 'bg-amber-300'}`} />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>

      {/* 카드 */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 flex-1 space-y-3">
        <div className="flex items-start justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900">{fmtDate(issue.date)}</span>
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
          <span className="text-xs text-gray-400 tabular-nums shrink-0">
            {issue.posts_total}건 / 평균 {issue.avg_7d}건
          </span>
        </div>

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
    </div>
  )
}

function WeeklyEntry({ w, t }: { w: WeeklyGallery; t: Record<string, string> }) {
  const kws = Array.isArray(w.keywords) ? w.keywords : []
  const hasCounts = w.daily_counts && Object.keys(w.daily_counts).length > 0
  const hasAI = w.ai_summary && w.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center shrink-0">
        <div className="w-3 h-3 rounded-full mt-1 bg-blue-300" />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>

      <Link href={`/weekly/${w.week_start}`} className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4 flex-1 space-y-3 hover:border-blue-200 transition-colors block">
        <div className="flex items-center justify-between gap-2">
          <span className="text-sm font-semibold text-blue-800">
            {t['gallery_detail.weekly_badge'] ?? '주간'} {fmtWeek(w.week_start, w.week_end)}
          </span>
          <span className="text-xs text-blue-400 tabular-nums">{w.total_posts}건</span>
        </div>

        {hasCounts && <WeeklyBarChart dailyCounts={w.daily_counts!} />}

        {hasAI && (
          <p className="text-sm text-blue-700 leading-relaxed">{w.ai_summary}</p>
        )}

        {kws.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {kws.slice(0, 5).map(([kw]) => (
              <span key={kw} className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">#{kw}</span>
            ))}
          </div>
        )}
      </Link>
    </div>
  )
}

export default async function GalleryDetailPage({ params }: Props) {
  const { id } = await params

  const [t, history] = await Promise.all([
    getTexts(),
    getGalleryHistory(id).catch(() => null),
  ])

  if (!history) notFound()

  const { gallery_name, issues, weeklies } = history

  // 합쳐서 날짜 역순 정렬
  const timeline: TimelineEntry[] = [
    ...issues.map(i => ({ kind: 'issue' as const, sortKey: i.date, data: i })),
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
          <div>
            {timeline.map(entry =>
              entry.kind === 'issue'
                ? <IssueEntry key={`i-${entry.data.date}-${(entry.data as DailyIssue).run_id}`} issue={entry.data as DailyIssue} t={t} />
                : <WeeklyEntry key={`w-${(entry.data as WeeklyGallery).week_start}`} w={entry.data as WeeklyGallery} t={t} />
            )}
          </div>
        )}
      </main>
    </div>
  )
}
