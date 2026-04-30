import Link from 'next/link'
import { api } from '@/lib/api'
import type { DailyIssue, TopPost } from '@/types'
import { notFound } from 'next/navigation'

interface Props { params: Promise<{ date: string }> }

function fmt(d: string) {
  const dt = new Date(d)
  return `${dt.getFullYear()}년 ${dt.getMonth() + 1}월 ${dt.getDate()}일`
}

function ScoreBadge({ score, hasIssue }: { score: number; hasIssue: boolean }) {
  const cls = hasIssue
    ? score >= 7 ? 'bg-red-100 text-red-700 border-red-200' : 'bg-orange-100 text-orange-700 border-orange-200'
    : 'bg-yellow-100 text-yellow-700 border-yellow-200'
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold border ${cls}`}>
      {hasIssue && <span className="w-1.5 h-1.5 rounded-full bg-current" />}
      이슈 점수 {score}/10
    </span>
  )
}

function PostList({ posts }: { posts: TopPost[] }) {
  return (
    <div className="space-y-1">
      {posts.map((p, i) => (
        <div key={i} className="flex items-start gap-2 text-sm">
          <span className="text-gray-300 w-4 shrink-0 mt-0.5">{i + 1}</span>
          <div className="min-w-0 flex-1">
            <a
              href={p.링크}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-800 hover:text-blue-600 hover:underline line-clamp-1"
            >
              {p.제목}
            </a>
            <div className="text-xs text-gray-400 mt-0.5 flex gap-2">
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
  const pct  = base > 0 ? ((issue.posts_total - base) / base * 100) : 0
  const kws  = Array.isArray(issue.keywords) ? issue.keywords : []
  const tops = Array.isArray(issue.top_posts) ? issue.top_posts : []

  return (
    <div className={`bg-white border rounded-xl p-5 space-y-4 ${
      issue.has_issue ? 'border-red-200' : issue.is_borderline ? 'border-yellow-200' : 'border-gray-200'
    }`}>
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3 flex-wrap">
          <h3 className="text-base font-semibold">{issue.gallery_name}</h3>
          <ScoreBadge score={issue.issue_score} hasIssue={issue.has_issue} />
        </div>
        <div className="text-right text-sm text-gray-500">
          <div><span className="font-mono font-medium text-gray-900">{issue.posts_total}건</span></div>
          <div className="text-xs">
            7일평균 {issue.avg_7d}건
            {issue.avg_same_weekday ? ` / 동요일평균 ${issue.avg_same_weekday}건` : ''}
            {pct !== 0 && (
              <span className={pct > 0 ? ' text-red-500' : ' text-green-500'}> ({pct > 0 ? '+' : ''}{pct.toFixed(0)}%)</span>
            )}
          </div>
        </div>
      </div>

      {issue.ai_summary && (
        <p className="text-sm text-gray-700 leading-relaxed border-l-2 border-gray-200 pl-3">
          {issue.ai_summary}
        </p>
      )}

      {kws.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 mb-1.5 uppercase tracking-wide font-medium">주요 키워드</p>
          <div className="flex flex-wrap gap-1.5">
            {kws.map(([kw, cnt]) => (
              <span key={kw} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full">
                #{kw} <span className="text-gray-400">{cnt}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {tops.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 mb-2 uppercase tracking-wide font-medium">화제 게시글 TOP {tops.length}</p>
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
    issues = await api.dailyByDate(date)
  } catch {
    notFound()
  }

  const sorted = [...issues].sort((a, b) => b.issue_score - a.issue_score)
  const issueList = sorted.filter(i => i.has_issue)
  const borderList = sorted.filter(i => !i.has_issue && i.is_borderline)
  const normalList = sorted.filter(i => !i.has_issue && !i.is_borderline)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link href="/" className="text-gray-400 hover:text-white text-sm shrink-0">← 홈</Link>
          <div>
            <h1 className="text-sm font-semibold">{fmt(date)} 일간 체크포인트</h1>
            {issueList.length > 0 && (
              <p className="text-xs text-red-400">이슈 {issueList.length}개 갤러리 감지</p>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {issueList.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wide">이슈 갤러리</h2>
            {issueList.map(i => <GalleryDetail key={i.gallery_id} issue={i} />)}
          </section>
        )}

        {borderList.length > 0 && (
          <section className="space-y-3">
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wide">주목 갤러리 (경계)</h2>
            {borderList.map(i => <GalleryDetail key={i.gallery_id} issue={i} />)}
          </section>
        )}

        {normalList.length > 0 && (
          <section>
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wide mb-2">정상 갤러리</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {normalList.map(i => (
                <div key={i.gallery_id} className="bg-white border border-gray-200 rounded-lg px-3 py-2 flex items-center justify-between">
                  <span className="text-sm text-gray-700 truncate">{i.gallery_name}</span>
                  <span className="text-xs text-gray-400 font-mono ml-2 shrink-0">{i.posts_total}건</span>
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
