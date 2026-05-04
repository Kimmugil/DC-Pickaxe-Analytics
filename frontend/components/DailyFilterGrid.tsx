'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { DailyIssue } from '@/types'
import { IssueCardFull } from '@/components/IssueCardFull'
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

export function DailyFilterGrid({ dateGroups, galleries, t }: Props) {
  const [galleryFilter, setGalleryFilter] = useState('all')

  const filtered = dateGroups
    .map(({ date, issues }) => ({
      date,
      issues: issues.filter(issue => {
        if (galleryFilter !== 'all' && issue.gallery_id !== galleryFilter) return false
        return true
      }),
    }))
    .filter(g => g.issues.length > 0)

  return (
    <div className="space-y-4">
      {/* 필터 바 */}
      <div className="flex flex-wrap gap-3 items-center bg-white border border-gray-200 rounded-lg px-4 py-3">
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

          <div className="space-y-3">
            {issues.map(issue => (
              <IssueCardFull
                key={`${issue.date}-${issue.gallery_id}`}
                issue={issue}
                t={t}
                collapsible={true}
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
