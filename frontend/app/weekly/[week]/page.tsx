import Link from 'next/link'
import type { WeeklyGallery, TopPost } from '@/types'
import { notFound } from 'next/navigation'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'
import { getWeeklyByWeek } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

interface Props { params: Promise<{ week: string }> }

function fmt(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
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
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function GalleryWeeklyCard({ g, t }: { g: WeeklyGallery; t: Record<string, string> }) {
  const kws = Array.isArray(g.keywords) ? g.keywords : []
  const tops = Array.isArray(g.top_posts) ? g.top_posts : []
  const hasCounts = g.daily_counts && Object.keys(g.daily_counts).length > 0
  const hasAI = g.ai_summary && g.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">{g.gallery_name}</h3>
        <span className="text-sm text-gray-500 tabular-nums">
          {t['weekly_detail.total_label'] ?? '총'}{' '}
          <span className="text-gray-900 font-semibold">{g.total_posts}</span>건
        </span>
      </div>

      {hasCounts && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-1">
            {t['weekly_detail.daily_posts_title'] ?? '일별 게시글'}
          </p>
          <WeeklyBarChart dailyCounts={g.daily_counts!} />
        </div>
      )}

      {hasAI && (
        <p className="text-sm text-gray-600 leading-relaxed">{g.ai_summary}</p>
      )}

      {kws.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-1.5">
            {t['common.keywords_title'] ?? '주요 키워드'}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {kws.slice(0, 8).map(([kw, cnt]) => (
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
            {tp(t, 'weekly_detail.top_posts_title', { count: tops.length }, '인기 게시글 TOP {count}')}
          </p>
          <PostList posts={tops} t={t} />
        </div>
      )}
    </div>
  )
}

export default async function WeeklyDetailPage({ params }: Props) {
  const { week } = await params

  const [t, data] = await Promise.all([
    getTexts(),
    getWeeklyByWeek(week).catch(() => null),
  ])

  if (!data) notFound()

  const { galleries, overall } = data
  const sorted = [...galleries].sort((a, b) => b.total_posts - a.total_posts)

  const suffix = t['weekly_detail.page_title_suffix'] ?? '주간 리포트'
  const titleStr = overall.week_start
    ? `${fmt(overall.week_start)} ~ ${fmt(overall.week_end ?? week)} ${suffix}`
    : `${week} ${suffix}`

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav
        back={{ href: '/weekly', label: t['nav.weekly'] ?? '주간 리포트' }}
        title={titleStr}
        subtitle={tp(t, 'common.gallery_count', { count: galleries.length }, '{count}개 갤러리')}
      />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">

        {overall.ai_summary && (
          <section className="bg-white border border-gray-200 rounded-lg p-5">
            <h2 className="text-xs text-gray-400 font-medium mb-3">
              {t['weekly_detail.summary_title'] ?? '종합 요약'}
            </h2>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {overall.ai_summary}
            </p>
          </section>
        )}

        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sorted.map(g => <GalleryWeeklyCard key={g.gallery_id} g={g} t={t} />)}
        </section>

      </main>
    </div>
  )
}
