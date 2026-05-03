'use client'
import { useState } from 'react'
import Link from 'next/link'
import type { TimelineItem } from '@/lib/data'
import type { DailyIssue } from '@/types'
import { galleryColor } from '@/lib/galleryColors'
import { tp } from '@/lib/textUtils'

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

const CAUSE_STYLE: Record<string, { bg: string; text: string }> = {
  컨텐츠: { bg: '#eff6ff', text: '#1d4ed8' },
  운영:   { bg: '#fff7ed', text: '#c2410c' },
  밸런스: { bg: '#fef9c3', text: '#854d0e' },
  버그:   { bg: '#fee2e2', text: '#991b1b' },
  결제:   { bg: '#fdf4ff', text: '#7e22ce' },
  화제:   { bg: '#f0fdf4', text: '#166534' },
}

const CATEGORY_LABEL: Record<string, string> = {
  balance: '밸런스', operation: '운영', bug: '버그', payment: '결제', content: '컨텐츠',
}
const CAUSE_LABEL: Record<string, string> = { ...CATEGORY_LABEL }

function FullIssueCard({ issue }: { issue: DailyIssue }) {
  const kws    = Array.isArray(issue.keywords)     ? issue.keywords     : []
  const tops   = Array.isArray(issue.top_posts)    ? issue.top_posts    : []
  const majors = Array.isArray(issue.major_issues) ? issue.major_issues : []
  const isHigh = issue.issue_score >= 7
  const c = galleryColor(issue.gallery_id)
  const cs = issue.category_scores

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 w-80 shrink-0 space-y-2.5">
      {/* 헤더 */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 flex-wrap min-w-0">
          <div className="text-xs font-semibold px-1.5 py-0.5 rounded truncate max-w-[140px]"
            style={{ backgroundColor: c.bg, color: c.text }}>
            {issue.gallery_name}
          </div>
          <span className={`text-xs font-bold tabular-nums ${isHigh ? 'text-red-600' : 'text-orange-500'}`}>
            {issue.issue_score}점
          </span>
          {issue.temperature_tag && (
            <span className="text-[11px] px-1 py-px bg-gray-100 text-gray-500 rounded">{issue.temperature_tag}</span>
          )}
          {issue.issue_cause && issue.issue_cause !== '기타' && (() => {
            const label = CAUSE_LABEL[issue.issue_cause!] ?? issue.issue_cause!
            const s = CAUSE_STYLE[label] ?? { bg: '#f9fafb', text: '#6b7280' }
            return (
              <span className="text-[10px] font-medium px-1 py-px rounded" style={{ backgroundColor: s.bg, color: s.text }}>
                {label}
              </span>
            )
          })()}
        </div>
        <span className="text-xs text-gray-400 tabular-nums shrink-0">{issue.posts_total}건</span>
      </div>

      {/* 헤드라인 */}
      {issue.headline && (
        <p className="text-xs font-semibold text-gray-800">{issue.headline}</p>
      )}

      {/* AI 요약 */}
      {issue.ai_summary && (
        <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">{issue.ai_summary}</p>
      )}

      {/* 카테고리 점수 바 */}
      {cs && (() => {
        const entries = Object.entries(cs) as [string, { score: number; summary: string }][]
        const active = entries.filter(([, v]) => v.score > 0)
        return active.length > 0 ? (
          <div className="space-y-1">
            {active.map(([k, v]) => (
              <div key={k} className="flex items-center gap-1.5 text-[10px]">
                <span className="text-gray-400 w-9 shrink-0">{CATEGORY_LABEL[k] ?? k}</span>
                <div className="flex gap-0.5">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="w-2.5 h-1.5 rounded-sm"
                      style={{ backgroundColor: i <= v.score ? '#f97316' : '#e5e7eb' }} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : null
      })()}

      {/* 주요 이슈 */}
      {majors.length > 0 && (
        <div className="space-y-1.5 pt-1.5 border-t border-gray-100">
          {majors.slice(0, 2).map((m, i) => (
            <div key={i} className="text-[11px]">
              <div className="flex items-center gap-1">
                <span className="font-semibold text-gray-700 truncate">{m.title}</span>
                {m.mention_count > 0 && <span className="text-gray-400 tabular-nums shrink-0">{m.mention_count}건</span>}
                {m.ref_url && <a href={m.ref_url} target="_blank" rel="noopener noreferrer" className="text-blue-400 shrink-0">↗</a>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 감정 분위기 */}
      {(issue.sentiment?.negative) && (
        <p className="text-[11px] text-red-600 line-clamp-2">{issue.sentiment.negative}</p>
      )}

      {/* 키워드 */}
      {kws.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {kws.slice(0, 5).map(([kw, cnt]) => (
            <span key={kw} className="text-[10px] px-1.5 py-px bg-gray-100 text-gray-600 rounded">
              #{kw} <span className="text-gray-400">{cnt}</span>
            </span>
          ))}
        </div>
      )}

      {/* top_posts (major_issues 없을 때만) */}
      {majors.length === 0 && tops.length > 0 && (
        <div className="space-y-1 pt-2 border-t border-gray-100">
          {tops.slice(0, 3).map((p, i) => (
            <div key={i} className="flex items-start gap-1.5 text-[11px]">
              <span className="text-gray-300 tabular-nums shrink-0">{i + 1}</span>
              <a href={p.링크} target="_blank" rel="noopener noreferrer"
                className="text-gray-700 hover:underline line-clamp-1 flex-1">{p.제목}</a>
              <span className="text-gray-400 tabular-nums shrink-0">댓글 {p.댓글수}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function IssueAccordionItem({
  item, isOpen, onToggle, t,
}: {
  item: Extract<TimelineItem, { kind: 'issue' }>
  isOpen: boolean
  onToggle: () => void
  t: Record<string, string>
}) {
  const isHigh = item.max_score >= 7
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center shrink-0">
        <div className={`w-3 h-3 rounded-full mt-1.5 shrink-0 ${isHigh ? 'bg-red-500' : 'bg-orange-400'}`} />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <div className="mb-4 flex-1 min-w-0">
        {/* Header / toggle */}
        <button
          onClick={onToggle}
          className="w-full bg-white border border-gray-200 rounded-lg p-4 text-left hover:border-gray-300 transition-colors"
        >
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900">{fmtDate(item.date)}</span>
            <div className="flex items-center gap-2">
              <span className={`text-xs font-medium tabular-nums ${isHigh ? 'text-red-600' : 'text-orange-500'}`}>
                {tp(t, 'common.issue_count', { count: item.issue_count }, '이슈 {count}개')}
              </span>
              <span className="text-gray-400 text-sm">{isOpen ? '▲' : '▼'}</span>
            </div>
          </div>
          {/* Gallery badges (collapsed summary) */}
          {!isOpen && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {item.galleries.map(g => {
                const c = galleryColor(g.id)
                return (
                  <span
                    key={g.id}
                    className="text-xs font-medium px-2 py-0.5 rounded"
                    style={{ backgroundColor: c.bg, color: c.text }}
                  >
                    {g.name} <span style={{ color: g.score >= 7 ? '#dc2626' : '#ea580c', fontWeight: 700 }}>{g.score}점</span>
                  </span>
                )
              })}
            </div>
          )}
        </button>

        {/* Expanded: horizontally scrollable cards */}
        {isOpen && (
          <div className="mt-2 overflow-x-auto pb-2">
            <div className="flex gap-3" style={{ minWidth: `${Math.max(item.issues.length * 300, 100)}px` }}>
              {item.issues.map(issue => (
                <FullIssueCard key={issue.gallery_id} issue={issue} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function WeeklyAccordionItem({
  item, isOpen, onToggle, t,
}: {
  item: Extract<TimelineItem, { kind: 'weekly' }>
  isOpen: boolean
  onToggle: () => void
  t: Record<string, string>
}) {
  return (
    <div className="flex gap-3">
      <div className="flex flex-col items-center shrink-0">
        <div className="w-3 h-3 rounded-full mt-1.5 bg-blue-300 shrink-0" />
        <div className="w-px flex-1 bg-gray-200 mt-1" />
      </div>
      <div className="mb-4 flex-1 min-w-0">
        <button
          onClick={onToggle}
          className="w-full bg-blue-50 border border-blue-100 rounded-lg p-4 text-left hover:border-blue-200 transition-colors"
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-sm font-semibold text-blue-800">
              {t['gallery_detail.weekly_badge'] ?? '주간'} {fmtWeek(item.week_start, item.week_end)}
            </span>
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-xs text-blue-400 tabular-nums">
                {tp(t, 'common.gallery_count', { count: item.gallery_count }, '{count}개 갤러리')}
              </span>
              <span className="text-blue-400 text-sm">{isOpen ? '▲' : '▼'}</span>
            </div>
          </div>
          {!isOpen && item.ai_summary && (
            <p className="text-sm text-blue-700 leading-relaxed mt-2 line-clamp-2">{item.ai_summary}</p>
          )}
        </button>

        {isOpen && (
          <div className="mt-2 bg-blue-50 border border-blue-100 rounded-lg p-4 space-y-3">
            {item.ai_summary && (
              <p className="text-sm text-blue-700 leading-relaxed whitespace-pre-line">{item.ai_summary}</p>
            )}
            <Link
              href={`/weekly/${item.week_start}`}
              className="inline-block text-xs text-blue-500 hover:underline"
            >
              {t['common.view_all'] ?? '전체 보기 →'}
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}

export function TimelineAccordion({ items, t }: { items: TimelineItem[]; t: Record<string, string> }) {
  const [openKeys, setOpenKeys] = useState<Set<string>>(new Set())

  function toggle(key: string) {
    setOpenKeys(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  return (
    <div>
      {items.map(item => {
        const key = item.kind === 'issue' ? `i-${item.date}` : `w-${item.date}`
        const isOpen = openKeys.has(key)
        return item.kind === 'issue'
          ? <IssueAccordionItem key={key} item={item} isOpen={isOpen} onToggle={() => toggle(key)} t={t} />
          : <WeeklyAccordionItem key={key} item={item} isOpen={isOpen} onToggle={() => toggle(key)} t={t} />
      })}
    </div>
  )
}
