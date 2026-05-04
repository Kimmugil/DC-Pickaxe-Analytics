'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import type { DailyIssue, WeeklyGallery, MonthlyGallery } from '@/types'
import { IssueCardFull } from '@/components/IssueCardFull'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'
import { CATEGORY_LABEL, CAUSE_STYLE, normalizeCause, CATEGORY_ORDER } from '@/lib/issueCategories'

type TimelineEntry =
  | { kind: 'issue';   sortKey: string; data: DailyIssue }
  | { kind: 'weekly';  sortKey: string; data: WeeklyGallery }
  | { kind: 'monthly'; sortKey: string; data: MonthlyGallery }

interface Props {
  timeline: TimelineEntry[]
  t: Record<string, string>
}

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

function fmtMonth(m: string) {
  if (!m) return ''
  const [y, mo] = m.split('-').map(Number)
  return `${y}년 ${mo}월`
}

// ── 주간 카드 ─────────────────────────────────────────────────────────

function CategoryBar({ cs }: { cs?: WeeklyGallery['category_scores'] }) {
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
            {label}
          </span>
        )
      })}
    </div>
  )
}

function WeeklyEntryCard({ w, t }: { w: WeeklyGallery; t: Record<string, string> }) {
  const kws  = Array.isArray(w.keywords)  ? w.keywords  : []
  const tops = Array.isArray(w.top_posts) ? w.top_posts : []
  const mis  = Array.isArray(w.major_issues) ? w.major_issues : []
  const hasCounts = w.daily_counts && Object.keys(w.daily_counts).length > 0
  const hasAI = w.ai_summary && w.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center shrink-0">
        <div className="w-3 h-3 rounded-full mt-1 bg-blue-300" />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4 flex-1 space-y-3">
        {/* 헤더 */}
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <span className="text-sm font-semibold text-blue-800">
              {t['gallery_detail.weekly_badge'] ?? '주간'} {fmtWeek(w.week_start, w.week_end)}
            </span>
            {w.headline && (
              <p className="text-xs text-blue-600 mt-0.5 leading-snug">{w.headline}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            <span className="text-xs text-blue-400 tabular-nums">{w.total_posts}건</span>
          </div>
        </div>

        {/* 카테고리 바 */}
        <CategoryBar cs={w.category_scores} />

        {/* 일별 게시글 차트 */}
        {hasCounts && <WeeklyBarChart dailyCounts={w.daily_counts!} />}

        {/* AI 요약 */}
        {hasAI && <p className="text-sm text-blue-700 leading-relaxed">{w.ai_summary}</p>}

        {/* 주요 이슈 */}
        {mis.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-blue-400 font-medium">{t['common.major_issues'] ?? '주요 이슈'}</p>
            {mis.map((mi, i) => (
              <div key={i} className="bg-white/60 rounded p-2 space-y-0.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-gray-800">{mi.title}</span>
                  {mi.mention_count > 0 && (
                    <span className="text-[11px] text-gray-400 tabular-nums shrink-0">{mi.mention_count}건</span>
                  )}
                </div>
                {mi.detail && <p className="text-xs text-gray-600 leading-relaxed">{mi.detail}</p>}
              </div>
            ))}
          </div>
        )}

        {/* 감성 */}
        {(w.sentiment?.positive || w.sentiment?.negative) && (
          <div className="grid grid-cols-2 gap-2">
            {w.sentiment.positive && (
              <div className="bg-green-50 rounded p-2">
                <p className="text-[10px] text-green-600 font-medium mb-0.5">{t['common.sentiment_positive'] ?? '긍정'}</p>
                <p className="text-xs text-green-800 leading-snug">{w.sentiment.positive}</p>
              </div>
            )}
            {w.sentiment.negative && (
              <div className="bg-red-50 rounded p-2">
                <p className="text-[10px] text-red-500 font-medium mb-0.5">{t['common.sentiment_negative'] ?? '부정'}</p>
                <p className="text-xs text-red-800 leading-snug">{w.sentiment.negative}</p>
              </div>
            )}
          </div>
        )}

        {/* 키워드 */}
        {kws.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {kws.slice(0, 8).map(([kw, cnt]) => (
              <span key={kw} className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">
                #{kw} <span className="text-blue-400 tabular-nums">{cnt}</span>
              </span>
            ))}
          </div>
        )}

        {/* 인기 게시글 */}
        {tops.length > 0 && (
          <div className="space-y-1 pt-1 border-t border-blue-100">
            <p className="text-xs text-blue-400 font-medium mb-1">
              {t['common.top_posts'] ?? '인기 게시글'} TOP {tops.length}
            </p>
            {tops.map((p, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
                <span className="text-gray-300 w-4 shrink-0 tabular-nums mt-0.5">{i + 1}</span>
                <div className="min-w-0 flex-1">
                  <a href={p.링크} target="_blank" rel="noopener noreferrer"
                    className="text-gray-800 hover:underline line-clamp-1">{p.제목}</a>
                  <div className="text-xs text-gray-400 mt-0.5 flex gap-2.5 tabular-nums">
                    <span>댓글 {p.댓글수}</span>
                    <span>추천 {p.추천수}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

// ── 월간 카드 ─────────────────────────────────────────────────────────

function MonthlyEntryCard({ m, t }: { m: MonthlyGallery; t: Record<string, string> }) {
  const kws  = Array.isArray(m.keywords)     ? m.keywords     : []
  const mis  = Array.isArray(m.major_issues) ? m.major_issues : []
  const tops = Array.isArray(m.top_posts)    ? m.top_posts    : []
  // category_scores가 JSON 문자열이면 파싱 시도
  const csRaw = m.category_scores
  const cs = (csRaw && typeof csRaw === 'object') ? csRaw : undefined
  const hasCounts = m.daily_counts && Object.keys(m.daily_counts).length > 0
  // 컬럼 순서 불일치로 ai_summary에 JSON 배열/객체가 들어온 경우 렌더링 건너뜀
  const aiSummaryClean = m.ai_summary && !m.ai_summary.trimStart().startsWith('[') && !m.ai_summary.trimStart().startsWith('{')
  const hasAI = aiSummaryClean && m.ai_summary !== '(이슈 없음 — AI 요약 제외)'
  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center shrink-0">
        <div className="w-3 h-3 rounded-full mt-1 bg-purple-300" />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <div className="bg-purple-50 border border-purple-100 rounded-lg p-4 mb-4 flex-1 space-y-3">
        {/* 헤더 */}
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <span className="text-sm font-semibold text-purple-800">
              {t['gallery_detail.monthly_badge'] ?? '월간'} {fmtMonth(m.month)}
            </span>
            {m.headline && (
              <p className="text-xs text-purple-600 mt-0.5 leading-snug">{m.headline}</p>
            )}
          </div>
          <div className="flex flex-col items-end gap-1 shrink-0">
            {m.total_posts !== undefined && (
              <span className="text-xs text-purple-400 tabular-nums">{m.total_posts}건</span>
            )}
            <span className="text-xs text-purple-500 tabular-nums">이슈 {m.issue_days}일</span>
          </div>
        </div>

        {/* 카테고리 점수 */}
        {cs && Object.keys(cs).length > 0 && (
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
                  {label}
                </span>
              )
            })}
          </div>
        )}

        {/* 게시글 분포 차트 */}
        {hasCounts && <WeeklyBarChart dailyCounts={m.daily_counts!} />}

        {/* AI 요약 */}
        {hasAI && (
          <p className="text-sm text-purple-700 leading-relaxed">{m.ai_summary}</p>
        )}

        {/* 주요 이슈 */}
        {mis.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-purple-400 font-medium">{t['common.major_issues'] ?? '주요 이슈'}</p>
            {mis.slice(0, 3).map((mi, i) => (
              <div key={i} className="bg-white/60 rounded p-2 space-y-0.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-semibold text-gray-800">{mi.title}</span>
                  {mi.mention_count > 0 && (
                    <span className="text-[11px] text-gray-400 tabular-nums shrink-0">{mi.mention_count}건</span>
                  )}
                </div>
                {mi.detail && <p className="text-xs text-gray-600 leading-relaxed">{mi.detail}</p>}
              </div>
            ))}
          </div>
        )}

        {/* 감성 (JSON 문자열로 오염된 경우 렌더링 제외) */}
        {(m.sentiment?.positive || m.sentiment?.negative) && (() => {
          const pos = m.sentiment!.positive
          const neg = m.sentiment!.negative
          const posClean = pos && !pos.trimStart().startsWith('{') && !pos.trimStart().startsWith('[')
          const negClean = neg && !neg.trimStart().startsWith('{') && !neg.trimStart().startsWith('[')
          if (!posClean && !negClean) return null
          return (
            <div className="grid grid-cols-2 gap-2">
              {posClean && (
                <div className="bg-green-50 rounded p-2">
                  <p className="text-[10px] text-green-600 font-medium mb-0.5">{t['common.sentiment_positive'] ?? '긍정'}</p>
                  <p className="text-xs text-green-800 leading-snug">{pos}</p>
                </div>
              )}
              {negClean && (
                <div className="bg-red-50 rounded p-2">
                  <p className="text-[10px] text-red-500 font-medium mb-0.5">{t['common.sentiment_negative'] ?? '부정'}</p>
                  <p className="text-xs text-red-800 leading-snug">{neg}</p>
                </div>
              )}
            </div>
          )
        })()}

        {/* 키워드 */}
        {kws.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {kws.slice(0, 8).map(([kw, cnt]) => (
              <span key={kw} className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-600 rounded">
                #{kw} <span className="text-purple-400 tabular-nums">{cnt}</span>
              </span>
            ))}
          </div>
        )}

        {/* TOP 게시글 */}
        {tops.length > 0 && (
          <div className="space-y-1 pt-1 border-t border-purple-100">
            <p className="text-xs text-purple-400 font-medium mb-1">{t['common.top_posts'] ?? '인기 게시글'} TOP {tops.length}</p>
            {tops.slice(0, 10).map((p, i) => (
              <div key={i} className="flex items-start gap-2 text-xs">
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
        )}
      </div>
    </div>
  )
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────────

export function GalleryTimelineClient({ timeline, t }: Props) {
  const [typeFilter, setTypeFilter] = useState<'all' | 'issue' | 'weekly' | 'monthly'>('all')

  // 해시 앵커 스크롤
  useEffect(() => {
    const hash = window.location.hash
    if (!hash) return
    const tryScroll = () => {
      const el = document.querySelector(hash)
      if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); return true }
      return false
    }
    if (!tryScroll()) {
      const timer = setTimeout(tryScroll, 300)
      return () => clearTimeout(timer)
    }
  }, [])

  const TYPE_OPTIONS = [
    { key: 'all' as const,     label: t['gallery_detail.filter_all']     ?? '전체' },
    { key: 'issue' as const,   label: t['gallery_detail.filter_daily']   ?? '일별' },
    { key: 'weekly' as const,  label: t['gallery_detail.filter_weekly']  ?? '주별' },
    { key: 'monthly' as const, label: t['gallery_detail.filter_monthly'] ?? '월별' },
  ]

  const filtered = timeline.filter(entry => {
    if (typeFilter !== 'all' && entry.kind !== typeFilter) return false
    return true
  })

  return (
    <div>
      {/* 타입 필터 */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {TYPE_OPTIONS.map(opt => (
          <button
            key={opt.key}
            onClick={() => setTypeFilter(opt.key)}
            className={`text-xs px-2.5 py-1 rounded-full transition-colors ${
              typeFilter === opt.key
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">
          {t['filter.no_results'] ?? '필터 조건에 맞는 이슈가 없습니다.'}
        </p>
      )}

      <div>
        {filtered.map(entry => {
          if (entry.kind === 'issue') {
            const issue = entry.data as DailyIssue
            return (
              <div
                key={`i-${issue.date}-${issue.run_id ?? ''}`}
                id={`issue-${issue.date}`}
                className="flex gap-4 scroll-mt-16"
              >
                <div className="flex flex-col items-center shrink-0">
                  <div className={`w-3 h-3 rounded-full mt-1 ${
                    issue.issue_score >= 7
                      ? 'bg-red-500'
                      : issue.has_issue
                      ? 'bg-orange-400'
                      : 'bg-amber-300'
                  }`} />
                  <div className="w-px flex-1 bg-gray-200 mt-1" />
                </div>
                <div className="flex-1 mb-4">
                  <IssueCardFull
                    issue={issue}
                    t={t}
                    collapsible={true}
                    headerLeft={
                      <span className="text-sm font-semibold text-gray-900">
                        {fmtDate(issue.date)}
                      </span>
                    }
                  />
                </div>
              </div>
            )
          }

          if (entry.kind === 'weekly') {
            const w = entry.data as WeeklyGallery
            return (
              <div
                key={`w-${w.week_start}`}
                id={`weekly-${w.week_start}`}
                className="scroll-mt-16"
              >
                <WeeklyEntryCard w={w} t={t} />
              </div>
            )
          }

          if (entry.kind === 'monthly') {
            const m = entry.data as MonthlyGallery
            return (
              <div
                key={`m-${m.month}`}
                id={`monthly-${m.month}`}
                className="scroll-mt-16"
              >
                <MonthlyEntryCard m={m} t={t} />
              </div>
            )
          }

          return null
        })}
      </div>
    </div>
  )
}
