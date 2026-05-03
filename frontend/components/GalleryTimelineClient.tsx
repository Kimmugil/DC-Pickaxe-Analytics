'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { DailyIssue, WeeklyGallery } from '@/types'
import { IssueCardFull } from '@/components/IssueCardFull'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'
import { FILTER_OPTIONS, CATEGORY_LABEL, normalizeCause } from '@/lib/issueCategories'

type TimelineEntry =
  | { kind: 'issue';  sortKey: string; data: DailyIssue }
  | { kind: 'weekly'; sortKey: string; data: WeeklyGallery }

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

function WeeklyEntryCard({ w, t }: { w: WeeklyGallery; t: Record<string, string> }) {
  const kws = Array.isArray(w.keywords) ? w.keywords : []
  const hasCounts = w.daily_counts && Object.keys(w.daily_counts).length > 0
  const hasAI = w.ai_summary && w.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center shrink-0">
        <div className="w-3 h-3 rounded-full mt-1 bg-blue-300" />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <Link
        href={`/weekly/${w.week_start}`}
        className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4 flex-1 space-y-3 hover:border-blue-200 transition-colors block"
      >
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
              <span key={kw} className="text-xs px-1.5 py-0.5 bg-blue-100 text-blue-600 rounded">
                #{kw}
              </span>
            ))}
          </div>
        )}
      </Link>
    </div>
  )
}

function matchesCategory(issue: DailyIssue, catKey: string): boolean {
  if (catKey === 'all') return true
  const cs = issue.category_scores
  if (cs && Object.keys(cs).length > 0) {
    const entry = cs[catKey as keyof typeof cs]
    if (entry && entry.score > 0) return true
  } else {
    if (!issue.issue_cause || issue.issue_cause === '기타') return true
  }
  return normalizeCause(issue.issue_cause) === CATEGORY_LABEL[catKey]
}

export function GalleryTimelineClient({ timeline, t }: Props) {
  const [catFilter, setCatFilter] = useState('all')

  const filtered = timeline.filter(entry => {
    if (entry.kind === 'weekly') return true // 주간 항목은 항상 표시
    return matchesCategory(entry.data as DailyIssue, catFilter)
  })

  return (
    <div>
      {/* 카테고리 필터 */}
      <div className="flex flex-wrap gap-1.5 mb-5">
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
        <p className="text-gray-400 text-sm text-center py-12">필터 조건에 맞는 이슈가 없습니다.</p>
      )}

      <div>
        {filtered.map(entry =>
          entry.kind === 'issue' ? (
            <div key={`i-${entry.data.date}-${(entry.data as DailyIssue).run_id}`} className="flex gap-4">
              <div className="flex flex-col items-center shrink-0">
                <div className={`w-3 h-3 rounded-full mt-1 ${
                  (entry.data as DailyIssue).issue_score >= 7
                    ? 'bg-red-500'
                    : (entry.data as DailyIssue).has_issue
                    ? 'bg-orange-400'
                    : 'bg-amber-300'
                }`} />
                <div className="w-px flex-1 bg-gray-200 mt-1" />
              </div>
              <div className="flex-1 mb-4">
                <IssueCardFull
                  issue={entry.data as DailyIssue}
                  t={t}
                  headerLeft={
                    <span className="text-sm font-semibold text-gray-900">
                      {fmtDate((entry.data as DailyIssue).date)}
                    </span>
                  }
                />
              </div>
            </div>
          ) : (
            <WeeklyEntryCard
              key={`w-${(entry.data as WeeklyGallery).week_start}`}
              w={entry.data as WeeklyGallery}
              t={t}
            />
          )
        )}
      </div>
    </div>
  )
}
