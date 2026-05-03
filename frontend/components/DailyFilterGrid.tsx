'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { DailyIssue } from '@/types'
import { IssueCardFull } from '@/components/IssueCardFull'
import { FILTER_OPTIONS, CATEGORY_LABEL, normalizeCause } from '@/lib/issueCategories'
import { tp } from '@/lib/textUtils'

interface DateGroup {
  date: string
  issues: DailyIssue[]
}

interface Props {
  dateGroups: DateGroup[]
  galleries: { id: string; name: string }[]
  t: Record<string, string>
}

function fmtDate(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

function matchesCategory(issue: DailyIssue, catKey: string): boolean {
  if (catKey === 'all') return true
  const cs = issue.category_scores
  // {} (빈 객체) 는 구버전 데이터로 취급 — Object.keys 로 실제 데이터 유무 구분
  if (cs && Object.keys(cs).length > 0) {
    const entry = cs[catKey as keyof typeof cs]
    if (entry && entry.score > 0) return true
  } else {
    // 구버전 데이터: issue_cause 없으면 전체 카테고리에 표시
    if (!issue.issue_cause || issue.issue_cause === '기타') return true
  }
  return normalizeCause(issue.issue_cause) === CATEGORY_LABEL[catKey]
}

export function DailyFilterGrid({ dateGroups, galleries, t }: Props) {
  const [catFilter, setCatFilter] = useState('all')
  const [galleryFilter, setGalleryFilter] = useState('all')

  const filtered = dateGroups
    .map(({ date, issues }) => ({
      date,
      issues: issues.filter(issue => {
        if (galleryFilter !== 'all' && issue.gallery_id !== galleryFilter) return false
        return matchesCategory(issue, catFilter)
      }),
    }))
    .filter(g => g.issues.length > 0)

  return (
    <div className="space-y-4">
      {/* 필터 바 */}
      <div className="flex flex-wrap gap-3 items-center bg-white border border-gray-200 rounded-lg px-4 py-3">
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

        <div className="w-px h-4 bg-gray-200 hidden sm:block" />

        <select
          value={galleryFilter}
          onChange={e => setGalleryFilter(e.target.value)}
          className="text-xs border border-gray-200 rounded px-2 py-1 outline-none focus:border-gray-400 bg-white text-gray-600"
        >
          <option value="all">전체 갤러리</option>
          {galleries.map(g => (
            <option key={g.id} value={g.id}>{g.name}</option>
          ))}
        </select>
      </div>

      {/* 결과 없음 */}
      {filtered.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">필터 조건에 맞는 이슈가 없습니다.</p>
      )}

      {/* 날짜 그룹별 카드 */}
      {filtered.map(({ date, issues }) => (
        <section key={date}>
          <div className="flex items-center gap-3 mb-3">
            <Link
              href={`/daily/${date}`}
              className="text-sm font-semibold text-gray-600 hover:text-gray-900 transition-colors whitespace-nowrap"
            >
              {fmtDate(date)}
            </Link>
            <div className="flex-1 h-px bg-gray-200" />
            <span className="text-xs text-gray-400 tabular-nums shrink-0">
              {tp(t, 'common.issue_count', { count: issues.filter(i => i.has_issue).length }, '이슈 {count}개')}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {issues.map(issue => (
              <IssueCardFull
                key={`${issue.date}-${issue.gallery_id}`}
                issue={issue}
                t={t}
                headerLeft={
                  <Link
                    href={`/gallery/${issue.gallery_id}`}
                    className="text-sm font-semibold text-gray-900 hover:underline"
                  >
                    {issue.gallery_name}
                  </Link>
                }
              />
            ))}
          </div>
        </section>
      ))}
    </div>
  )
}
