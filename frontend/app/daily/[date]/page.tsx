import Link from 'next/link'
import type { DailyIssue, TopPost } from '@/types'
import { notFound } from 'next/navigation'
import { getDailyByDate } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

interface Props { params: Promise<{ date: string }> }

function fmt(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

const CAUSE_STYLE: Record<string, string> = {
  컨텐츠: 'text-blue-600 bg-blue-50',
  운영:   'text-orange-600 bg-orange-50',
  화제:   'text-purple-600 bg-purple-50',
}

function IssueCauseBadge({ cause }: { cause: string }) {
  const cls = CAUSE_STYLE[cause] ?? 'text-gray-500 bg-gray-100'
  return (
    <span className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${cls}`}>
      {cause}
    </span>
  )
}

function ScoreDot({ score, hasIssue }: { score: number; hasIssue: boolean }) {
  const cls = hasIssue
    ? score >= 7 ? 'bg-red-500' : 'bg-orange-400'
    : 'bg-amber-400'
  return <span className={`w-2 h-2 rounded-full shrink-0 ${cls}`} />
}

function ScoreTag({ score, hasIssue }: { score: number; hasIssue: boolean }) {
  const cls = hasIssue
    ? score >= 7 ? 'text-red-600' : 'text-orange-500'
    : 'text-amber-600'
  return (
    <span className={`text-xs font-semibold tabular-nums ${cls}`}>{score}점</span>
  )
}

function PostList({ posts, t }: { posts: TopPost[]; t: Record<string, string> }) {
  return (
    <div className="space-y-2">
      {posts.map((p, i) => (
        <div key={i} className="flex items-start gap-2.5 text-sm">
          <span className="text-gray-300 w-4 shrink-0 mt-0.5 tabular-nums">{i + 1}</span>
          <div className="min-w-0 flex-1">
            <a
              href={p.링크}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-800 hover:underline line-clamp-1"
            >
              {p.제목}
            </a>
            <div className="text-xs text-gray-400 mt-0.5 flex gap-2.5 tabular-nums">
              <span>{tp(t, 'common.comment_count', { count: p.댓글수 }, '댓글 {count}')}</span>
              <span>{tp(t, 'common.like_count', { count: p.추천수 }, '추천 {count}')}</span>
              {p.조회수 > 0 && (
                <span>{tp(t, 'common.view_count', { count: p.조회수.toLocaleString() }, '조회 {count}')}</span>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function GalleryDetail({ issue, t }: { issue: DailyIssue; t: Record<string, string> }) {
  const base = Math.max(issue.avg_same_weekday ?? 0, issue.avg_7d)
  const pct = base > 0 ? ((issue.posts_total - base) / base) * 100 : 0
  const kws = Array.isArray(issue.keywords) ? issue.keywords : []
  const tops = Array.isArray(issue.top_posts) ? issue.top_posts : []

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2.5 flex-wrap">
          <ScoreDot score={issue.issue_score} hasIssue={issue.has_issue} />
          <h3 className="text-sm font-semibold text-gray-900">{issue.gallery_name}</h3>
          {issue.is_borderline && !issue.has_issue && (
            <span className="text-xs text-gray-400">
              {t['common.borderline_label'] ?? '경계'}
            </span>
          )}
          <ScoreTag score={issue.issue_score} hasIssue={issue.has_issue} />
          {issue.temperature_tag && (
            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
              {issue.temperature_tag}
            </span>
          )}
          {issue.issue_cause && issue.issue_cause !== '기타' && (
            <IssueCauseBadge cause={issue.issue_cause} />
          )}
        </div>
        <div className="text-right text-sm text-gray-500">
          <span className="font-semibold text-gray-900 tabular-nums">{issue.posts_total}건</span>
          <span className="text-xs ml-2 text-gray-400 tabular-nums">
            {tp(t, 'daily_detail.avg_7d', { count: issue.avg_7d }, '7일평균 {count}건')}
            {issue.avg_same_weekday
              ? ` · ${tp(t, 'daily_detail.avg_weekday', { count: issue.avg_same_weekday }, '동요일 {count}건')}`
              : ''}
            {pct !== 0 && (
              <span className={pct > 0 ? ' text-red-500' : ' text-green-500'}>
                {' '}({pct > 0 ? '+' : ''}{pct.toFixed(0)}%)
              </span>
            )}
          </span>
        </div>
      </div>
      {(issue.has_issue || issue.is_borderline) && issue.recent_issue_days !== undefined && issue.recent_issue_days > 0 && (
        <p className="text-xs text-amber-600 tabular-nums">
          {tp(t, 'daily_detail.recent_issue_days', { count: issue.recent_issue_days }, '최근 4주 중 {count}일 이슈')}
        </p>
      )}

      {issue.ai_summary && (
        <p className="text-sm text-gray-600 leading-relaxed">{issue.ai_summary}</p>
      )}

      {kws.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-1.5">
            {t['common.keywords_title'] ?? '주요 키워드'}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {kws.map(([kw, cnt]) => (
              <span key={kw} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                #{kw} <span className="text-gray-400 tabular-nums">{cnt}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {tops.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-2">
            {tp(t, 'daily_detail.top_posts_title', { count: tops.length }, '화제 게시글 TOP {count}')}
          </p>
          <PostList posts={tops} t={t} />
        </div>
      )}
    </div>
  )
}

export default async function DailyDetailPage({ params }: Props) {
  const { date } = await params

  const [t, issues] = await Promise.all([
    getTexts(),
    getDailyByDate(date).catch(() => null),
  ])

  if (issues === null) notFound()

  const sorted = [...issues].sort((a, b) => b.issue_score - a.issue_score)
  const issueList = sorted.filter(i => i.has_issue)
  const borderList = sorted.filter(i => !i.has_issue && i.is_borderline)
  const normalList = sorted.filter(i => !i.has_issue && !i.is_borderline)

  const pageTitle = `${fmt(date)} ${t['daily_detail.page_title_suffix'] ?? '일간 체크포인트'}`
  const pageSubtitle = issueList.length > 0
    ? tp(t, 'daily_detail.issue_detected', { count: issueList.length }, '이슈 {count}개 갤러리 감지')
    : undefined

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav back={{ href: '/daily', label: t['nav.daily'] ?? '일간 이슈' }} title={pageTitle} subtitle={pageSubtitle} />

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {issueList.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-xs text-gray-400 font-medium">
              {t['daily_detail.section_issue'] ?? '이슈 갤러리'}
            </h2>
            {issueList.map(i => <GalleryDetail key={i.gallery_id} issue={i} t={t} />)}
          </section>
        )}

        {borderList.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-xs text-gray-400 font-medium">
              {t['daily_detail.section_borderline'] ?? '주목 갤러리 (경계)'}
            </h2>
            {borderList.map(i => <GalleryDetail key={i.gallery_id} issue={i} t={t} />)}
          </section>
        )}

        {normalList.length > 0 && (
          <section>
            <h2 className="text-xs text-gray-400 font-medium mb-2">
              {t['daily_detail.section_normal'] ?? '정상 갤러리'}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {normalList.map(i => (
                <div
                  key={i.gallery_id}
                  className="bg-white border border-gray-200 rounded-lg px-3 py-2 flex items-center justify-between"
                >
                  <span className="text-sm text-gray-700 truncate">{i.gallery_name}</span>
                  <span className="text-xs text-gray-400 font-medium tabular-nums ml-2 shrink-0">
                    {i.posts_total}건
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {issues.length === 0 && (
          <div className="text-center py-20 text-gray-400 text-sm">
            {t['common.no_data'] ?? '데이터 없음'}
          </div>
        )}
      </main>
    </div>
  )
}
