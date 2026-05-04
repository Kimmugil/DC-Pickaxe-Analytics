'use client'
import { useState, useMemo } from 'react'
import Link from 'next/link'
import { galleryColor } from '@/lib/galleryColors'
import { normalizeCause, CAUSE_STYLE } from '@/lib/issueCategories'

interface GalleryEntry {
  id: string
  name: string
  score: number
  cause?: string
}

interface Props {
  issuesByDate: Record<string, GalleryEntry[]>
  weeklyDates: string[]
  t?: Record<string, string>
  /** 갤러리 상세 페이지에서 사용 시 설정 — 주간 이벤트를 페이지 내 앵커로 연결 */
  galleryId?: string
}

function toDateStr(d: Date) {
  return [
    d.getUTCFullYear(),
    String(d.getUTCMonth() + 1).padStart(2, '0'),
    String(d.getUTCDate()).padStart(2, '0'),
  ].join('-')
}

function CauseBadge({ cause }: { cause?: string }) {
  if (!cause) return null
  const label = normalizeCause(cause)
  const style = CAUSE_STYLE[label]
  if (!style || label === '기타') return null
  return (
    <span
      className="text-[8px] leading-tight px-0.5 rounded shrink-0 font-semibold"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      {label}
    </span>
  )
}

export function CalendarClient({ issuesByDate, weeklyDates, t = {}, galleryId }: Props) {
  const now = new Date()
  const todayStr = toDateStr(now)
  const curYear  = now.getUTCFullYear()
  const curMonth = now.getUTCMonth() + 1

  const [viewYear,  setViewYear]  = useState(curYear)
  const [viewMonth, setViewMonth] = useState(curMonth)

  const weeklySet = useMemo(() => new Set(weeklyDates), [weeklyDates])
  const isCurrentMonth = viewYear === curYear && viewMonth === curMonth

  function prevMonth() {
    if (viewMonth === 1) { setViewYear(y => y - 1); setViewMonth(12) }
    else setViewMonth(m => m - 1)
  }
  function nextMonth() {
    if (isCurrentMonth) return
    if (viewMonth === 12) { setViewYear(y => y + 1); setViewMonth(1) }
    else setViewMonth(m => m + 1)
  }

  const firstDOW   = new Date(Date.UTC(viewYear, viewMonth - 1, 1)).getUTCDay()
  const daysInMonth = new Date(Date.UTC(viewYear, viewMonth, 0)).getUTCDate()
  const totalCells  = Math.ceil((firstDOW + daysInMonth) / 7) * 7
  const calStart    = new Date(Date.UTC(viewYear, viewMonth - 1, 1 - firstDOW))

  const cells = Array.from({ length: totalCells }, (_, i) => {
    const d = new Date(calStart)
    d.setUTCDate(calStart.getUTCDate() + i)
    return toDateStr(d)
  })
  const weeks: string[][] = []
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7))

  return (
    <div>
      {/* Month navigation */}
      <div className="flex items-center justify-between mb-3">
        <button
          onClick={prevMonth}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-800 transition-colors text-lg leading-none"
          aria-label="이전 달"
        >‹</button>
        <h3 className="text-sm font-semibold text-gray-700">{viewYear}년 {viewMonth}월</h3>
        <button
          onClick={nextMonth}
          disabled={isCurrentMonth}
          className="p-1.5 rounded hover:bg-gray-100 text-gray-500 hover:text-gray-800 transition-colors text-lg leading-none disabled:opacity-25 disabled:cursor-not-allowed"
          aria-label="다음 달"
        >›</button>
      </div>

      {/* Day headers */}
      <div className="grid grid-cols-7 mb-1 border-b border-gray-100 pb-1">
        {['일','월','화','수','목','금','토'].map((label, i) => (
          <div key={label} className={`text-center text-[11px] font-medium py-1 ${i===0?'text-red-400':i===6?'text-blue-400':'text-gray-400'}`}>
            {label}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      {weeks.map((week, wi) => (
        <div key={wi} className="grid grid-cols-7 gap-px mb-px">
          {week.map((dateStr, di) => {
            const [cy, cm, cd] = dateStr.split('-').map(Number)
            const inMonth  = cm === viewMonth && cy === viewYear
            const isToday  = dateStr === todayStr
            const isFuture = dateStr > todayStr
            const isSun = di === 0, isSat = di === 6
            const galleries = inMonth && !isFuture ? (issuesByDate[dateStr] ?? []) : []
            const hasIssue  = galleries.length > 0
            const hasWeekly = inMonth && !isFuture && weeklySet.has(dateStr)

            return (
              <div
                key={dateStr}
                className={`min-h-[72px] p-1 rounded transition-colors ${
                  isToday ? 'bg-blue-50 ring-1 ring-blue-200' : ''
                }`}
              >
                {/* Date number */}
                <div className="flex items-center justify-between mb-0.5">
                  <span className={`text-[11px] font-semibold ${
                    !inMonth  ? 'text-gray-200' :
                    isToday   ? 'text-blue-600' :
                    isFuture  ? 'text-gray-300' :
                    isSun ? 'text-red-500' : isSat ? 'text-blue-500' : 'text-gray-700'
                  }`}>
                    {cd}
                    {isToday && <span className="ml-1 text-[9px] font-normal text-blue-400">{t['calendar.today'] ?? '오늘'}</span>}
                  </span>
                </div>

                {/* 주간 리포트 이벤트 바 */}
                {hasWeekly && (
                  galleryId ? (
                    <a
                      href={`#weekly-${dateStr}`}
                      className="block w-full text-left text-[9px] leading-tight px-1 py-0.5 rounded-sm mb-0.5 font-semibold truncate"
                      style={{ backgroundColor: '#dbeafe', color: '#1e40af' }}
                    >
                      {t['calendar.weekly_label'] ?? '주간 리포트'}
                    </a>
                  ) : (
                    <div
                      className="block w-full text-left text-[9px] leading-tight px-1 py-0.5 rounded-sm mb-0.5 font-semibold truncate"
                      style={{ backgroundColor: '#dbeafe', color: '#1e40af' }}
                    >
                      {t['calendar.weekly_label'] ?? '주간 리포트'}
                    </div>
                  )
                )}

                {/* 갤러리 이슈 배지 — 개별 클릭 */}
                {hasIssue && (
                  <div className="flex flex-col gap-px">
                    {galleries.slice(0, 3).map(g => {
                      const c = galleryColor(g.id)
                      return (
                        <Link
                          key={g.id}
                          href={`/gallery/${g.id}#issue-${dateStr}`}
                          className="flex items-center gap-0.5 rounded-sm px-0.5 py-px"
                          style={{ backgroundColor: c.bg }}
                        >
                          <span
                            className="text-[9px] leading-tight truncate flex-1 font-semibold"
                            style={{ color: c.text }}
                          >
                            {g.name}
                          </span>
                          <span
                            className="text-[9px] tabular-nums shrink-0 font-bold"
                            style={{ color: g.score >= 7 ? '#dc2626' : '#ea580c' }}
                          >
                            {g.score}
                          </span>
                          <CauseBadge cause={g.cause} />
                        </Link>
                      )
                    })}
                    {galleries.length > 3 && (
                      <span className="text-[9px] text-gray-400 px-0.5 leading-tight">
                        +{galleries.length - 3}
                      </span>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ))}

      <div className="flex items-center gap-4 mt-2 pt-2 border-t border-gray-100 text-[10px] text-gray-400">
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: '#ede9fe' }} />
          {t['calendar.legend_issue'] ?? '이슈 (갤러리별 색상)'}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="inline-block w-10 h-3 rounded-sm" style={{ backgroundColor: '#dbeafe' }} />
          {t['calendar.legend_weekly'] ?? '주간 리포트'}
        </span>
        <span className="flex items-center gap-1.5">
          <span className="text-[8px] px-0.5 rounded font-semibold" style={{ backgroundColor: '#fef9c3', color: '#854d0e' }}>{t['calendar.legend_category_sample'] ?? '밸런스'}</span>
          {t['calendar.legend_category'] ?? '카테고리'}
        </span>
      </div>
    </div>
  )
}
