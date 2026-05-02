import Link from 'next/link'
import type { DailyIssue, WeeklyGallery } from '@/types'
import { notFound } from 'next/navigation'
import { getGalleryHistory } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'

interface Props { params: Promise<{ id: string }> }

function fmtFull(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}/${day}`
}

const CAUSE_STYLE: Record<string, string> = {
  컨텐츠: 'text-blue-600 bg-blue-50',
  운영:   'text-orange-600 bg-orange-50',
  화제:   'text-purple-600 bg-purple-50',
}

function ScoreBadge({ score }: { score: number }) {
  const cls = score >= 7 ? 'text-red-600' : score >= 5 ? 'text-orange-500' : 'text-amber-500'
  return <span className={`text-xs font-semibold tabular-nums ${cls}`}>{score}점</span>
}

function IssueCard({ issue, t }: { issue: DailyIssue; t: Record<string, string> }) {
  const kws = Array.isArray(issue.keywords) ? issue.keywords : []
  const tops = Array.isArray(issue.top_posts) ? issue.top_posts : []
  const isIssue = issue.has_issue

  return (
    <div className={`bg-white border rounded-lg p-4 space-y-3 ${isIssue ? 'border-gray-200' : 'border-gray-100'}`}>
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-900">{fmtFull(issue.date)}</span>
          <ScoreBadge score={issue.issue_score} />
          {!isIssue && (
            <span className="text-xs text-gray-400">{t['common.borderline_label'] ?? '경계'}</span>
          )}
          {issue.temperature_tag && (
            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
              {issue.temperature_tag}
            </span>
          )}
          {issue.issue_cause && issue.issue_cause !== '기타' && (
            <span className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${CAUSE_STYLE[issue.issue_cause] ?? 'text-gray-500 bg-gray-100'}`}>
              {issue.issue_cause}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400 tabular-nums shrink-0">
          {issue.posts_total}건
          {issue.avg_7d > 0 && ` (평균 ${issue.avg_7d}건)`}
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
        <div className="space-y-1">
          {tops.slice(0, 3).map((p, i) => (
            <div key={i} className="flex items-start gap-2 text-xs">
              <span className="text-gray-300 w-3 shrink-0 tabular-nums">{i + 1}</span>
              <a
                href={p.링크}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-700 hover:underline line-clamp-1 flex-1"
              >
                {p.제목}
              </a>
              <span className="text-gray-400 shrink-0 tabular-nums">댓글 {p.댓글수}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function WeeklyCard({ w, t }: { w: WeeklyGallery; t: Record<string, string> }) {
  const kws = Array.isArray(w.keywords) ? w.keywords : []
  const hasCounts = w.daily_counts && Object.keys(w.daily_counts).length > 0

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-900">
          {fmtShort(w.week_start)} ~ {fmtShort(w.week_end)}
        </span>
        <span className="text-xs text-gray-400 tabular-nums">{w.total_posts}건</span>
      </div>

      {hasCounts && <WeeklyBarChart dailyCounts={w.daily_counts!} />}

      {w.ai_summary && w.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)' && (
        <p className="text-sm text-gray-600 leading-relaxed">{w.ai_summary}</p>
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

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav back={{ href: '/gallery', label: t['nav.gallery'] ?? '갤러리' }} title={gallery_name} />

      <main className="max-w-5xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">

          {/* ── 이슈 이력 ── */}
          <section>
            <h2 className="text-xs font-medium text-gray-400 mb-3">
              {t['gallery_detail.issue_history'] ?? '이슈 이력'}
            </h2>
            {issues.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-16">
                {t['gallery_detail.no_issues'] ?? '기록된 이슈 없음'}
              </p>
            ) : (
              <div className="space-y-3">
                {issues.map(i => <IssueCard key={`${i.date}-${i.run_id}`} issue={i} t={t} />)}
              </div>
            )}
          </section>

          {/* ── 주간 요약 ── */}
          <section>
            <h2 className="text-xs font-medium text-gray-400 mb-3">
              {t['gallery_detail.weekly_summary'] ?? '주간 요약'}
            </h2>
            {weeklies.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-16">
                {t['common.no_data'] ?? '데이터 없음'}
              </p>
            ) : (
              <div className="space-y-3">
                {weeklies.map(w => (
                  <Link key={w.week_start} href={`/weekly/${w.week_start}`}>
                    <WeeklyCard w={w} t={t} />
                  </Link>
                ))}
              </div>
            )}
          </section>

        </div>
      </main>
    </div>
  )
}
