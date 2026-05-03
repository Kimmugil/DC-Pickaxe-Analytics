'use client'
import { useState, useEffect } from 'react'
import type { DailyIssue } from '@/types'
import { IssueCardFull } from '@/components/IssueCardFull'
import { FILTER_OPTIONS, CATEGORY_LABEL, normalizeCause } from '@/lib/issueCategories'

interface Props {
  issueList: DailyIssue[]
  borderList: DailyIssue[]
  t: Record<string, string>
  labels: {
    sectionIssue: string
    sectionBorderline: string
  }
}

function matchesCategory(issue: DailyIssue, catKey: string): boolean {
  if (catKey === 'all') return true
  const cs = issue.category_scores
  if (cs) {
    const entry = cs[catKey as keyof typeof cs]
    if (entry && entry.score > 0) return true
  } else {
    // 구버전 데이터: category_scores 없으면 issue_cause만 비교
    // cause가 없으면 전체 카테고리에 표시 (구버전 데이터 숨기지 않음)
    if (!issue.issue_cause || issue.issue_cause === '기타') return true
  }
  return normalizeCause(issue.issue_cause) === CATEGORY_LABEL[catKey]
}

export function DailyDetailFilter({ issueList, borderList, t, labels }: Props) {
  const [catFilter, setCatFilter] = useState('all')

  // 해시 앵커로 스크롤 이동
  useEffect(() => {
    const hash = window.location.hash
    if (!hash) return
    const tryScroll = () => {
      const el = document.querySelector(hash)
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'start' })
        return true
      }
      return false
    }
    if (!tryScroll()) {
      // DOM이 아직 렌더링 안 됐을 경우 retry
      const timer = setTimeout(tryScroll, 200)
      return () => clearTimeout(timer)
    }
  }, [])

  const filteredIssues = issueList.filter(i => matchesCategory(i, catFilter))
  const filteredBorder = borderList.filter(i => matchesCategory(i, catFilter))
  const totalVisible   = filteredIssues.length + filteredBorder.length

  return (
    <div className="space-y-6">
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

      {totalVisible === 0 && (
        <p className="text-gray-400 text-sm text-center py-8">
          {t['filter.no_results'] ?? '필터 조건에 맞는 이슈가 없습니다.'}
        </p>
      )}

      {filteredIssues.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xs text-gray-400 font-medium">{labels.sectionIssue}</h2>
          {filteredIssues.map(i => (
            <div key={i.gallery_id} id={`issue-${i.gallery_id}`} className="scroll-mt-16">
              <IssueCardFull issue={i} t={t} />
            </div>
          ))}
        </section>
      )}

      {filteredBorder.length > 0 && (
        <section className="space-y-3">
          <h2 className="text-xs text-gray-400 font-medium">{labels.sectionBorderline}</h2>
          {filteredBorder.map(i => (
            <div key={i.gallery_id} id={`issue-${i.gallery_id}`} className="scroll-mt-16">
              <IssueCardFull issue={i} t={t} />
            </div>
          ))}
        </section>
      )}
    </div>
  )
}
