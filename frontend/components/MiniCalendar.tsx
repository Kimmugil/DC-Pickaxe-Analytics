'use client'
import { useState, useMemo } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface GalleryEntry {
  id: string
  name: string
  score: number
  cause?: string
}

interface Props {
  issuesByDate: Record<string, GalleryEntry[]>
  weeklyDates: string[]
}

function toDateStr(d: Date) {
  return [
    d.getUTCFullYear(),
    String(d.getUTCMonth() + 1).padStart(2, '0'),
    String(d.getUTCDate()).padStart(2, '0'),
  ].join('-')
}

export function MiniCalendar({ issuesByDate, weeklyDates }: Props) {
  const pathname = usePathname()
  const now = new Date()
  const todayStr = toDateStr(now)
  const curYear  = now.getUTCFullYear()
  const curMonth = now.getUTCMonth() + 1

  const [viewYear,  setViewYear]  = useState(curYear)
  const [viewMonth, setViewMonth] = useState(curMonth)

  // 갤러리 상세 페이지 감지
  const galleryMatch = pathname.match(/^\/gallery\/([^/]+)$/)
  const galleryId = galleryMatch ? decodeURIComponent(galleryMatch[1]) : null

  const isCurrentMonth = viewYear === curYear && viewMonth === curMonth
  const weeklySet = useMemo(() => new Set(weeklyDates), [weeklyDates])

  function prevMonth() {
    if (viewMonth === 1) { setViewYear(y => y - 1); setViewMonth(12) }
    else setViewMonth(m => m - 1)
  }
  function nextMonth() {
    if (isCurrentMonth) return
    if (viewMonth === 12) { setViewYear(y => y + 1); setViewMonth(1) }
    else setViewMonth(m => m + 1)
  }

  const firstDOW    = new Date(Date.UTC(viewYear, viewMonth - 1, 1)).getUTCDay()
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
    <div className="px-2 pt-2 pb-1.5 border-b border-gray-100">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-1">
        <button
          onClick={prevMonth}
          className="text-gray-400 hover:text-gray-600 text-xs leading-none w-4 text-center"
          aria-label="이전 달"
        >‹</button>
        <span className="text-[10px] font-semibold text-gray-500 tabular-nums">
          {viewYear}.{String(viewMonth).padStart(2, '0')}
        </span>
        <button
          onClick={nextMonth}
          disabled={isCurrentMonth}
          className="text-gray-400 hover:text-gray-600 text-xs leading-none w-4 text-center disabled:opacity-25"
          aria-label="다음 달"
        >›</button>
      </div>

      {/* 요일 헤더 */}
      <div className="grid grid-cols-7 mb-0.5">
        {['일', '월', '화', '수', '목', '금', '토'].map((d, i) => (
          <div
            key={d}
            className={`text-center text-[8px] font-medium ${
              i === 0 ? 'text-red-300' : i === 6 ? 'text-blue-300' : 'text-gray-300'
            }`}
          >
            {d}
          </div>
        ))}
      </div>

      {/* 날짜 그리드 */}
      {weeks.map((week, wi) => (
        <div key={wi} className="grid grid-cols-7">
          {week.map((dateStr, di) => {
            const [cy, cm, cd] = dateStr.split('-').map(Number)
            const inMonth  = cm === viewMonth && cy === viewYear
            const isFuture = dateStr > todayStr
            const isToday  = dateStr === todayStr
            const isSun    = di === 0
            const isSat    = di === 6

            // 이벤트 계산
            let galleries = (inMonth && !isFuture) ? (issuesByDate[dateStr] ?? []) : []
            if (galleryId) {
              galleries = galleries.filter(g => g.id === galleryId)
            }
            const hasIssue  = galleries.length > 0
            // 주간 리포트: 비갤러리 페이지에서만 표시
            const hasWeekly = !galleryId && inMonth && !isFuture && weeklySet.has(dateStr)

            // 최고 점수
            const maxScore = hasIssue ? Math.max(...galleries.map(g => g.score)) : 0

            // 클릭 href
            let href: string | null = null
            if (hasIssue) {
              href = galleryId ? `#issue-${dateStr}` : `/timeline#i-${dateStr}`
            }

            const dotRow = (hasIssue || hasWeekly) && (
              <div className="flex justify-center gap-px mt-px">
                {hasWeekly && (
                  <div className="w-1 h-1 rounded-full bg-blue-300 shrink-0" />
                )}
                {hasIssue && (
                  <div className={`w-1 h-1 rounded-full shrink-0 ${
                    maxScore >= 7 ? 'bg-red-400' : 'bg-orange-300'
                  }`} />
                )}
              </div>
            )

            const dateNum = (
              <div className={`flex flex-col items-center py-px rounded ${
                isToday ? 'bg-blue-50' : ''
              }`}>
                <span className={`text-[9px] leading-tight tabular-nums ${
                  !inMonth  ? 'text-gray-200' :
                  isFuture  ? 'text-gray-300' :
                  isToday   ? 'text-blue-600 font-bold' :
                  isSun ? 'text-red-400' : isSat ? 'text-blue-400' : 'text-gray-600'
                }`}>
                  {cd}
                </span>
                {dotRow}
              </div>
            )

            if (!inMonth || (!hasIssue && !hasWeekly)) {
              return <div key={dateStr}>{dateNum}</div>
            }

            if (href && href.startsWith('#')) {
              return (
                <a
                  key={dateStr}
                  href={href}
                  className="hover:bg-gray-50 rounded cursor-pointer"
                  title={dateStr}
                >
                  {dateNum}
                </a>
              )
            }

            if (href) {
              return (
                <Link
                  key={dateStr}
                  href={href}
                  className="hover:bg-gray-50 rounded"
                  title={dateStr}
                >
                  {dateNum}
                </Link>
              )
            }

            return <div key={dateStr}>{dateNum}</div>
          })}
        </div>
      ))}
    </div>
  )
}
