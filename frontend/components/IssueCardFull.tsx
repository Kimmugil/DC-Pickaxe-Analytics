'use client'
import { useState } from 'react'
import type { DailyIssue } from '@/types'
import { CATEGORY_ORDER, CATEGORY_LABEL, CAUSE_STYLE, normalizeCause } from '@/lib/issueCategories'
import { tp } from '@/lib/textUtils'

// ── 카테고리 점수 바 ──────────────────────────────────────────────────

function CategoryBar({ scores }: { scores: DailyIssue['category_scores'] }) {
  if (!scores) return null
  const active = CATEGORY_ORDER.filter(k => (scores[k]?.score ?? 0) > 0)
  if (!active.length) return null
  return (
    <div className="space-y-1.5">
      {active.map(k => {
        const v = scores[k]
        return (
          <div key={k} className="text-xs">
            <div className="flex items-center gap-2">
              <span className="text-gray-400 w-10 shrink-0">{CATEGORY_LABEL[k]}</span>
              <div className="flex gap-0.5 shrink-0">
                {[1, 2, 3].map(i => (
                  <div key={i} className="w-3 h-2 rounded-sm"
                    style={{ backgroundColor: i <= v.score ? '#f97316' : '#e5e7eb' }} />
                ))}
              </div>
              {v.summary && (
                <span className="text-gray-500 leading-snug">{v.summary}</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

// ── 공통 이슈 카드 본문 ───────────────────────────────────────────────

interface IssueCardFullProps {
  issue: DailyIssue
  t: Record<string, string>
  /** 헤더 왼쪽 영역 커스텀 (생략 시 갤러리명 텍스트) */
  headerLeft?: React.ReactNode
  /** 통계 우측 표시 여부 (기본 true) */
  showStats?: boolean
  /** 토글 접기 모드 — 헤드라인·AI요약까지만 기본 표시, 상세는 버튼으로 펼침 */
  collapsible?: boolean
}

export function IssueCardFull({ issue, t, headerLeft, showStats = true, collapsible = false }: IssueCardFullProps) {
  const [expanded, setExpanded] = useState(!collapsible)

  const kws    = Array.isArray(issue.keywords)     ? issue.keywords     : []
  const tops   = Array.isArray(issue.top_posts)    ? issue.top_posts    : []
  const majors = Array.isArray(issue.major_issues) ? issue.major_issues : []
  const isHigh = issue.issue_score >= 7

  const causeLabel = normalizeCause(issue.issue_cause)
  const causeStyle = causeLabel ? (CAUSE_STYLE[causeLabel] ?? CAUSE_STYLE['기타']) : null

  const base = Math.max(issue.avg_same_weekday ?? 0, issue.avg_7d)
  const pct  = base > 0 ? ((issue.posts_total - base) / base) * 100 : 0

  const hasDetails = !!(
    issue.category_scores ||
    majors.length > 0 ||
    issue.sentiment?.positive ||
    issue.sentiment?.negative ||
    kws.length > 0 ||
    tops.length > 0
  )

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">

      {/* 헤더 */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          {headerLeft ?? (
            <span className="text-sm font-semibold text-gray-900">{issue.gallery_name}</span>
          )}
          <span className={`text-xs font-bold tabular-nums ${isHigh ? 'text-red-600' : issue.has_issue ? 'text-orange-500' : 'text-amber-500'}`}>
            {issue.issue_score}점
          </span>
          {!issue.has_issue && issue.is_borderline && (
            <span className="text-xs text-gray-400">{t['common.borderline_label'] ?? '경계'}</span>
          )}
          {issue.temperature_tag && (
            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
              {issue.temperature_tag}
            </span>
          )}
          {causeLabel && causeLabel !== '기타' && causeStyle && (
            <span className="text-[11px] font-medium px-1.5 py-0.5 rounded"
              style={{ backgroundColor: causeStyle.bg, color: causeStyle.text }}>
              {causeLabel}
            </span>
          )}
        </div>
        {showStats && (
          <div className="text-right text-xs text-gray-500 shrink-0">
            <span className="font-semibold text-gray-700 tabular-nums">{issue.posts_total}건</span>
            <span className="text-gray-400 ml-1 tabular-nums">
              {tp(t, 'daily_detail.avg_7d', { count: issue.avg_7d }, '7일평균 {count}건')}
              {pct !== 0 && (
                <span className={pct > 0 ? ' text-red-500' : ' text-green-500'}>
                  {' '}({pct > 0 ? '+' : ''}{pct.toFixed(0)}%)
                </span>
              )}
            </span>
          </div>
        )}
      </div>

      {/* 최근 이슈 빈도 */}
      {issue.recent_issue_days !== undefined && issue.recent_issue_days > 0 && (
        <p className="text-xs text-amber-600 tabular-nums">
          {tp(t, 'daily_detail.recent_issue_days', { count: issue.recent_issue_days }, '최근 4주 중 {count}일 이슈')}
        </p>
      )}

      {/* 헤드라인 */}
      {issue.headline && (
        <p className="text-sm font-semibold text-gray-800">{issue.headline}</p>
      )}

      {/* AI 요약 */}
      {issue.ai_summary && (
        <p className="text-sm text-gray-600 leading-relaxed">{issue.ai_summary}</p>
      )}

      {/* 토글 버튼 (collapsible 모드에서 상세 내용 있을 때) */}
      {collapsible && hasDetails && (
        <button
          onClick={() => setExpanded(v => !v)}
          className="text-xs text-gray-400 hover:text-gray-600 transition-colors flex items-center gap-1 pt-1 border-t border-gray-100 w-full"
        >
          <span>{expanded ? (t['common.collapse'] ?? '접기') : (t['common.expand'] ?? '더 보기')}</span>
          <span className={`transition-transform ${expanded ? 'rotate-180' : ''}`}>▾</span>
        </button>
      )}

      {/* 상세 내용 (collapsible 모드에서는 expanded일 때만) */}
      {(!collapsible || expanded) && (
        <>
          {/* 카테고리 점수 바 */}
          {issue.category_scores && (
            <div className="pt-1 border-t border-gray-100">
              <CategoryBar scores={issue.category_scores} />
            </div>
          )}

          {/* 주요 이슈 */}
          {majors.length > 0 && (
            <div className="space-y-2.5 pt-2 border-t border-gray-100">
              {majors.map((m, i) => (
                <div key={i} className="text-xs space-y-0.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-semibold text-gray-800">{m.title}</span>
                    {m.mention_count > 0 && (
                      <span className="text-gray-400 tabular-nums">언급 {m.mention_count}건</span>
                    )}
                    {m.ref_url && (
                      <a href={m.ref_url} target="_blank" rel="noopener noreferrer"
                        className="text-blue-400 hover:underline">↗</a>
                    )}
                  </div>
                  {m.detail && <p className="text-gray-500 leading-relaxed">{m.detail}</p>}
                </div>
              ))}
            </div>
          )}

          {/* 감정 분위기 */}
          {(issue.sentiment?.positive || issue.sentiment?.negative) && (
            <div className="flex flex-col gap-1 pt-2 border-t border-gray-100 text-xs">
              {issue.sentiment.positive && (
                <p className="text-green-700">
                  <span className="font-medium">긍정</span> {issue.sentiment.positive}
                </p>
              )}
              {issue.sentiment.negative && (
                <p className="text-red-600">
                  <span className="font-medium">부정</span> {issue.sentiment.negative}
                </p>
              )}
            </div>
          )}

          {/* 키워드 */}
          {kws.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {kws.slice(0, 8).map(([kw, cnt]) => (
                <span key={kw} className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                  #{kw} <span className="text-gray-400 tabular-nums">{cnt}</span>
                </span>
              ))}
            </div>
          )}

          {/* 상위 게시글 (major_issues 없을 때만) */}
          {majors.length === 0 && tops.length > 0 && (
            <div className="space-y-1 pt-2 border-t border-gray-100">
              {tops.slice(0, 3).map((p, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className="text-gray-300 w-3 tabular-nums shrink-0">{i + 1}</span>
                  <a href={p.링크} target="_blank" rel="noopener noreferrer"
                    className="text-gray-700 hover:underline line-clamp-1 flex-1">
                    {p.제목}
                  </a>
                  <span className="text-gray-400 tabular-nums shrink-0">댓글 {p.댓글수}</span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
