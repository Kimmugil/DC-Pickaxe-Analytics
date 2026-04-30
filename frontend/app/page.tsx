import Link from 'next/link'
import { api } from '@/lib/api'
import type { DailyIssue } from '@/types'

function fmt(d: string) {
  if (!d) return ''
  const dt = new Date(d)
  return `${dt.getMonth() + 1}월 ${dt.getDate()}일`
}

function ScoreBadge({ score, hasIssue, isBorderline }: {
  score: number; hasIssue: boolean; isBorderline?: boolean
}) {
  if (score < 4) return null
  const cls = hasIssue
    ? score >= 7
      ? 'bg-red-50 text-red-700 border-red-200'
      : 'bg-orange-50 text-orange-700 border-orange-200'
    : 'bg-yellow-50 text-yellow-700 border-yellow-200'
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${cls}`}>
      {hasIssue && <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />}
      {score}점
    </span>
  )
}

function GalleryCard({ issue }: { issue: DailyIssue }) {
  const base = Math.max(issue.avg_same_weekday ?? 0, issue.avg_7d)
  const pct  = base > 0 ? ((issue.posts_total - base) / base * 100) : 0
  const pctStr  = pct > 0 ? `+${pct.toFixed(0)}%` : `${pct.toFixed(0)}%`
  const pctColor = pct > 100 ? 'text-red-600' : pct > 30 ? 'text-orange-500' : 'text-gray-400'
  const kws = Array.isArray(issue.keywords) ? issue.keywords.slice(0, 4) : []

  return (
    <div className={`bg-white border rounded-lg p-4 space-y-2 ${
      issue.has_issue ? 'border-red-200' : issue.is_borderline ? 'border-yellow-200' : 'border-gray-200'
    }`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-medium truncate">{issue.gallery_name}</span>
          <ScoreBadge score={issue.issue_score} hasIssue={issue.has_issue} isBorderline={issue.is_borderline} />
        </div>
        <div className="text-right shrink-0">
          <span className="text-sm font-mono">{issue.posts_total}건</span>
          <span className={`text-xs ml-1 ${pctColor}`}>{pctStr}</span>
        </div>
      </div>
      {issue.ai_summary && (
        <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">{issue.ai_summary}</p>
      )}
      {kws.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {kws.map(([kw]) => (
            <span key={kw} className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">#{kw}</span>
          ))}
        </div>
      )}
    </div>
  )
}

function CalendarStrip({
  issueDates, weeklyDates,
}: { issueDates: string[]; weeklyDates: string[] }) {
  const today = new Date()
  const todayStr = today.toISOString().slice(0, 10)
  const issueSet  = new Set(issueDates)
  const weeklySet = new Set(weeklyDates)

  const days = Array.from({ length: 30 }, (_, i) => {
    const d = new Date(today)
    d.setDate(d.getDate() - (29 - i))
    return d.toISOString().slice(0, 10)
  })

  return (
    <div className="overflow-x-auto">
      <div className="flex gap-0.5 pb-1" style={{ minWidth: 'max-content' }}>
        {days.map(day => {
          const hasIssue  = issueSet.has(day)
          const hasWeekly = weeklySet.has(day)
          const isToday   = day === todayStr
          const m = parseInt(day.slice(5, 7))
          const d = parseInt(day.slice(8, 10))
          const href = hasIssue ? `/daily/${day}` : hasWeekly ? `/weekly/${day}` : null

          const inner = (
            <div className={`flex flex-col items-center gap-0.5 px-2 py-1.5 rounded min-w-[38px] select-none
              ${isToday ? 'bg-blue-600 text-white' : href ? 'hover:bg-gray-100 cursor-pointer' : 'text-gray-400 cursor-default'}
            `}>
              <span className="text-[9px] leading-none">{m}월</span>
              <span className="text-sm font-medium leading-none">{d}</span>
              <div className="flex gap-0.5 h-1.5">
                {hasIssue  && <span className="w-1.5 h-1.5 rounded-full bg-red-400" />}
                {hasWeekly && <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />}
              </div>
            </div>
          )

          return href ? (
            <Link key={day} href={href}>{inner}</Link>
          ) : (
            <div key={day}>{inner}</div>
          )
        })}
      </div>
    </div>
  )
}

export default async function HomePage() {
  const [calendar, latestDaily, latestWeekly] = await Promise.allSettled([
    api.calendar(),
    api.dailyLatest(),
    api.weeklyLatest(),
  ])

  const cal         = calendar.status === 'fulfilled' ? calendar.value : { issue_dates: [], weekly_dates: [] }
  const dailyInfo   = latestDaily.status === 'fulfilled' ? latestDaily.value : {}
  const weeklyInfo  = latestWeekly.status === 'fulfilled' ? latestWeekly.value : {}

  const latestDate  = dailyInfo.date
  const issueCount  = dailyInfo.issue_gallery_count

  let dailyIssues: DailyIssue[] = []
  if (latestDate) {
    try { dailyIssues = await api.dailyByDate(latestDate) } catch {}
  }

  const issues = dailyIssues.filter(i => i.has_issue || i.is_borderline)
  const normal = dailyIssues.filter(i => !i.has_issue && !i.is_borderline)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gray-900 text-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-lg">⛏️</span>
            <div>
              <h1 className="text-sm font-semibold leading-tight">디씨곡괭이 정련소</h1>
              <p className="text-[11px] text-gray-400 leading-tight">DC인사이드 키우기 장르 동향 분석</p>
            </div>
          </div>
          <div className="text-right text-xs text-gray-400 space-y-0.5">
            {latestDate && <div>{fmt(latestDate)} 기준</div>}
            {issueCount != null && <div>이슈 {issueCount}개 갤러리</div>}
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-8">

        {/* Calendar */}
        <section>
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-xs font-medium text-gray-400 uppercase tracking-wide">최근 30일</h2>
            <div className="flex items-center gap-3 text-[11px] text-gray-400">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />이슈
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-blue-400 inline-block" />주간
              </span>
            </div>
          </div>
          <div className="bg-white border border-gray-200 rounded-lg p-3">
            <CalendarStrip issueDates={cal.issue_dates} weeklyDates={cal.weekly_dates} />
          </div>
        </section>

        {/* Latest daily */}
        {latestDate && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold">{fmt(latestDate)} 일간 현황</h2>
              <Link href={`/daily/${latestDate}`} className="text-sm text-blue-600 hover:underline">
                전체 보기 →
              </Link>
            </div>
            {issues.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {issues.map(i => <GalleryCard key={i.gallery_id} issue={i} />)}
              </div>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg p-10 text-center text-gray-400 text-sm">
                이슈 없음
              </div>
            )}
            {normal.length > 0 && (
              <p className="mt-2 text-xs text-gray-400">그 외 {normal.length}개 갤러리 정상</p>
            )}
          </section>
        )}

        {/* Weekly link */}
        {weeklyInfo.week_start && (
          <section>
            <div className="bg-white border border-gray-200 rounded-lg p-4 flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-400 mb-0.5">최신 주간 리포트</p>
                <p className="font-medium text-sm">
                  {fmt(weeklyInfo.week_start!)} ~ {fmt(weeklyInfo.week_end!)}
                </p>
              </div>
              <Link
                href={`/weekly/${weeklyInfo.week_start}`}
                className="px-4 py-2 bg-gray-900 text-white text-sm rounded-lg hover:bg-gray-700 transition-colors"
              >
                리포트 보기
              </Link>
            </div>
          </section>
        )}

      </main>
    </div>
  )
}
