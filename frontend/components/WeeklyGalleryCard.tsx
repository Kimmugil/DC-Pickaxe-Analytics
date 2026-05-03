'use client'
import type { WeeklyGallery, TopPost } from '@/types'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'
import { CAUSE_STYLE, normalizeCause, CATEGORY_ORDER, FILTER_OPTIONS, CATEGORY_LABEL } from '@/lib/issueCategories'
import { useState } from 'react'

function PostList({ posts, t }: { posts: TopPost[]; t: Record<string, string> }) {
  return (
    <div className="space-y-1.5">
      {posts.map((p, i) => (
        <div key={i} className="flex items-start gap-2 text-sm">
          <span className="text-gray-300 w-4 shrink-0 tabular-nums mt-0.5">{i + 1}</span>
          <div className="min-w-0 flex-1">
            <a href={p.링크} target="_blank" rel="noopener noreferrer"
              className="text-gray-800 hover:underline line-clamp-1">
              {p.제목}
            </a>
            <div className="text-xs text-gray-400 mt-0.5 flex gap-2.5 tabular-nums">
              <span>댓글 {p.댓글수}</span>
              <span>추천 {p.추천수}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

function CategoryBar({ g }: { g: WeeklyGallery }) {
  const cs = g.category_scores
  if (!cs || Object.keys(cs).length === 0) return null
  const hasAny = CATEGORY_ORDER.some(k => cs[k]?.score > 0)
  if (!hasAny) return null
  return (
    <div className="flex gap-1.5 flex-wrap">
      {CATEGORY_ORDER.map(k => {
        const entry = cs[k]
        if (!entry || entry.score === 0) return null
        const label = CATEGORY_LABEL[k]
        const style = CAUSE_STYLE[label]
        if (!style) return null
        return (
          <span
            key={k}
            className="text-[11px] px-1.5 py-0.5 rounded font-medium"
            style={{ backgroundColor: style.bg, color: style.text }}
            title={entry.summary || undefined}
          >
            {label} {entry.score > 0 ? '·'.repeat(entry.score) : ''}
          </span>
        )
      })}
    </div>
  )
}

export function WeeklyGalleryCard({ g, t }: { g: WeeklyGallery; t: Record<string, string> }) {
  const kws   = Array.isArray(g.keywords)  ? g.keywords  : []
  const tops  = Array.isArray(g.top_posts) ? g.top_posts : []
  const mis   = Array.isArray(g.major_issues) ? g.major_issues : []
  const hasCounts = g.daily_counts && Object.keys(g.daily_counts).length > 0
  const hasAI = g.ai_summary && g.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'
  const causeLabelKo = g.top_cause ? normalizeCause(g.top_cause) : null
  const causeStyle = causeLabelKo && CAUSE_STYLE[causeLabelKo] ? CAUSE_STYLE[causeLabelKo] : null

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-gray-900">{g.gallery_name}</h3>
          {g.headline && (
            <p className="text-xs text-gray-500 mt-0.5 leading-snug">{g.headline}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-sm text-gray-500 tabular-nums">
            {t['weekly_detail.total_label'] ?? '총'}{' '}
            <span className="text-gray-900 font-semibold">{g.total_posts}</span>건
          </span>
          {causeStyle && causeLabelKo && (
            <span
              className="text-[11px] px-1.5 py-0.5 rounded font-medium"
              style={{ backgroundColor: causeStyle.bg, color: causeStyle.text }}
            >
              {causeLabelKo}
            </span>
          )}
        </div>
      </div>

      {/* 카테고리 점수 바 */}
      <CategoryBar g={g} />

      {/* 바 차트 */}
      {hasCounts && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-1">
            {t['weekly_detail.daily_posts_title'] ?? '일별 게시글'}
          </p>
          <WeeklyBarChart dailyCounts={g.daily_counts!} />
        </div>
      )}

      {/* AI 요약 */}
      {hasAI && (
        <p className="text-sm text-gray-600 leading-relaxed">{g.ai_summary}</p>
      )}

      {/* 주요 이슈 */}
      {mis.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-400 font-medium">주요 이슈</p>
          {mis.map((mi, i) => (
            <div key={i} className="bg-gray-50 rounded p-2.5 space-y-1">
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-semibold text-gray-800">{mi.title}</span>
                {mi.mention_count > 0 && (
                  <span className="text-[11px] text-gray-400 tabular-nums shrink-0">{mi.mention_count}건</span>
                )}
              </div>
              {mi.detail && (
                <p className="text-xs text-gray-600 leading-relaxed">{mi.detail}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 감성 분석 */}
      {(g.sentiment?.positive || g.sentiment?.negative) && (
        <div className="grid grid-cols-2 gap-2">
          {g.sentiment.positive && (
            <div className="bg-green-50 rounded p-2">
              <p className="text-[10px] text-green-600 font-medium mb-0.5">긍정</p>
              <p className="text-xs text-green-800 leading-snug">{g.sentiment.positive}</p>
            </div>
          )}
          {g.sentiment.negative && (
            <div className="bg-red-50 rounded p-2">
              <p className="text-[10px] text-red-500 font-medium mb-0.5">부정</p>
              <p className="text-xs text-red-800 leading-snug">{g.sentiment.negative}</p>
            </div>
          )}
        </div>
      )}

      {/* 키워드 */}
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

      {/* TOP 게시글 */}
      {tops.length > 0 && (
        <div>
          <p className="text-xs text-gray-400 font-medium mb-2">
            인기 게시글 TOP {tops.length}
          </p>
          <PostList posts={tops} t={t} />
        </div>
      )}
    </div>
  )
}

// ── 카테고리 필터 래퍼 ──────────────────────────────────────────────

function matchesCategory(g: WeeklyGallery, catKey: string): boolean {
  if (catKey === 'all') return true
  const cs = g.category_scores
  if (cs && Object.keys(cs).length > 0) {
    const entry = cs[catKey as keyof typeof cs]
    if (entry && entry.score > 0) return true
  } else {
    if (!g.top_cause || g.top_cause === '기타') return true
  }
  return normalizeCause(g.top_cause) === CATEGORY_LABEL[catKey]
}

interface FilterProps {
  galleries: WeeklyGallery[]
  t: Record<string, string>
}

export function WeeklyGalleryFilter({ galleries, t }: FilterProps) {
  const [catFilter, setCatFilter] = useState('all')
  const filtered = galleries.filter(g => matchesCategory(g, catFilter))

  return (
    <div className="space-y-4">
      {/* 카테고리 필터 */}
      <div className="flex flex-wrap gap-1.5">
        {FILTER_OPTIONS.map(opt => (
          <button
            key={opt.key}
            onClick={() => setCatFilter(opt.key)}
            className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
              catFilter === opt.key
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-8">
          {t['filter.no_results'] ?? '필터 조건에 맞는 이슈가 없습니다.'}
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered.map(g => (
          <WeeklyGalleryCard key={g.gallery_id} g={g} t={t} />
        ))}
      </div>
    </div>
  )
}
