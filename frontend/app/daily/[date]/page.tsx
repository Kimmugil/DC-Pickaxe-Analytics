import Link from 'next/link'
import type { DailyIssue, TopPost } from '@/types'
import { notFound } from 'next/navigation'
import { getDailyByDate } from '@/lib/data'
import { Nav } from '@/components/Nav'

interface Props { params: Promise<{ date: string }> }

function fmt(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

function ScoreDot({ score, hasIssue }: { score: number; hasIssue: boolean }) {
  const cls = hasIssue
    ? score >= 7
      ? 'bg-red-500'
      : 'bg-orange-400'
    : 'bg-amber-400'
  return <span className={`w-2 h-2 rounded-full shrink-0 ${cls}`} />
}

function ScoreTag({ score, hasIssue }: { score: number; hasIssue: boolean }) {
  const cls = hasIssue
    ? score >= 7
      ? 'text-red-600'
      : 'text-orange-500'
    : 'text-amber-600'
  return (
    <span className={`text-xs font-semibold tabular-nums ${cls}`}>
      {score}점
    </span>
  )
}

function PostList({ posts }: { posts: TopPost[] }) {
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
              className="text-gray-800 hover:text-gray-900 hover:underline line-clamp-1"
            >
              {p.제목}
            </a>
            <div className="text-xs text-gray-400 mt-0.5 flex gap-2.5 tabular-nums">
              <span>댓글 {p.댓글수}</span>
              <span>추천 {p.추천수}</span>
              {p.조회수 > 0 && <span>조회 {p.조회수.toLocaleString()}</span>}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function GalleryDetail({ issue }: { issue: DailyIssue }) {
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
            <span className="text-xs text-gray-400">경계</span>
          )}
          <ScoreTag score={issue.issue_score} hasIssue={issue.has_issue} />
        </div>
        <div className="text-right text-sm text-gray-500">
          <span className="font-semibold text-gray-900 tabular-nums">{issue.posts_total}건</span>
          <span className="text-xs ml-2 text-gray-400 tabular-nums">
            7일평균 {issue.avg_7d}건
            {issue.avg_same_weekday ? ` · 동요일 ${issue.avg_same_weekday}건` : ''}
            {pct !== 0 && (
              <span className={pct > 0 ? ' text-red-500' : ' text-green-500'}>
                {' '}
                ({pct > 0 ? '+' : ''}{pct.toFixed(0)}%)
              </span>
            )}
          </span>
        </div>
      </div>

      {issue.ai_summary && (
        <p className="text-sm text-gray-600 leading-relaxed">{issue.ai_summary}</p>
      )}

      {kws.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-1.5">주요 키워드</p>
          <div className="flex flex-wrap gap-1.5">
            {kws.map(([kw, cnt]) => (
              <span
                key={kw}
                className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
              >
                #{kw} <span className="text-gray-400 tabular-nums">{cnt}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {tops.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-2">
            화제 게시글 TOP {tops.length}
          </p>
          <PostList posts={tops} />
        </div>
      )}
    </div>
  )
}

export default async function DailyDetailPage({ params }: Props) {
  const { date } = await params
  let issues: DailyIssue[] = []
  try {
    issues = await getDailyByDate(date)
  } catch {
    notFound()
  }

  const sorted = [...issues].sort((a, b) => b.issue_score - a.issue_score)
  const issueList = sorted.filter(i => i.has_issue)
  const borderList = sorted.filter(i => !i.has_issue && i.is_borderline)
  const normalList = sorted.filter(i => !i.has_issue && !i.is_borderline)

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav
        back={{ href: '/reports', label: '리포트 목록' }}
        title={`${fmt(date)} 일간 체크포인트`}
        subtitle={issueList.length > 0 ? `이슈 ${issueList.length}개 갤러리 감지` : undefined}
      />

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {issueList.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-xs text-gray-400 font-medium">이슈 갤러리</h2>
            {issueList.map(i => (
              <GalleryDetail key={i.gallery_id} issue={i} />
            ))}
          </section>
        )}

        {borderList.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-xs text-gray-400 font-medium">주목 갤러리 (경계)</h2>
            {borderList.map(i => (
              <GalleryDetail key={i.gallery_id} issue={i} />
            ))}
          </section>
        )}

        {normalList.length > 0 && (
          <section>
            <h2 className="text-xs text-gray-400 font-medium mb-2">정상 갤러리</h2>
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
          <div className="text-center py-20 text-gray-400 text-sm">데이터 없음</div>
        )}
      </main>
    </div>
  )
}
