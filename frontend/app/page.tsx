import Link from 'next/link'
import type { DailyIssue, WeeklyGallery } from '@/types'
import {
  getCalendarData,
  getGalleryList,
  getRecentDailyIssues,
  getLatestWeeklyOverall,
} from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'

function fmtFull(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}
function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

// ── 미니 달력 ─────────────────────────────────────────────────────────────

function MiniCalendar({
  issueDates,
  weeklyDates,
  t,
}: {
  issueDates: string[]
  weeklyDates: string[]
  t: Record<string, string>
}) {
  const now = new Date()
  const todayStr = [
    now.getUTCFullYear(),
    String(now.getUTCMonth() + 1).padStart(2, '0'),
    String(now.getUTCDate()).padStart(2, '0'),
  ].join('-')

  const issueSet  = new Set(issueDates)
  const weeklySet = new Set(weeklyDates)
  const [ty, tm, td] = todayStr.split('-').map(Number)
  const todayDOW = new Date(Date.UTC(ty, tm - 1, td)).getUTCDay()
  const calStart = new Date(Date.UTC(ty, tm - 1, td - todayDOW - 14))

  const toDateStr = (dt: Date) =>
    [dt.getUTCFullYear(),
     String(dt.getUTCMonth() + 1).padStart(2, '0'),
     String(dt.getUTCDate()).padStart(2, '0'),
    ].join('-')

  const weeks: string[][] = Array.from({ length: 4 }, (_, w) =>
    Array.from({ length: 7 }, (_, d) => {
      const dt = new Date(calStart)
      dt.setUTCDate(calStart.getUTCDate() + w * 7 + d)
      return toDateStr(dt)
    }),
  )

  return (
    <div>
      <div className="grid grid-cols-7 mb-1">
        {['일','월','화','수','목','금','토'].map((label, i) => (
          <div key={label} className={`text-center text-[11px] py-0.5 font-medium ${i===0?'text-red-400':i===6?'text-blue-400':'text-gray-400'}`}>
            {label}
          </div>
        ))}
      </div>
      {weeks.map((week, wi) => (
        <div key={wi} className="grid grid-cols-7 mb-0.5">
          {week.map((dateStr, di) => {
            const dayNum = parseInt(dateStr.slice(8), 10)
            const isToday  = dateStr === todayStr
            const isFuture = dateStr > todayStr
            const hasIssue  = issueSet.has(dateStr)
            const hasWeekly = weeklySet.has(dateStr)
            const isSun = di === 0, isSat = di === 6
            const href = !isFuture
              ? (hasIssue ? `/daily/${dateStr}` : hasWeekly ? `/weekly/${dateStr}` : null)
              : null

            const cell = (
              <div className={`flex flex-col items-center py-1 rounded select-none ${isToday?'bg-blue-600':href?'hover:bg-gray-100 cursor-pointer':''}`}>
                <span className={`text-xs font-medium leading-none ${isToday?'text-white':isFuture?'text-gray-300':isSun?'text-red-500':isSat?'text-blue-500':'text-gray-800'}`}>
                  {dayNum}
                </span>
                {isToday
                  ? <span className="text-[9px] text-blue-200 leading-none mt-0.5">오늘</span>
                  : <div className="flex gap-px mt-1 h-1.5 items-center">
                      {hasIssue  && <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />}
                      {hasWeekly && <span className="w-1.5 h-1.5 rounded-full bg-blue-300 shrink-0" />}
                      {!hasIssue && !hasWeekly && <span className="w-1.5 h-1.5 shrink-0" />}
                    </div>
                }
              </div>
            )
            return href ? <Link key={dateStr} href={href}>{cell}</Link> : <div key={dateStr}>{cell}</div>
          })}
        </div>
      ))}
      <div className="flex items-center gap-4 mt-2 pt-2 border-t border-gray-100 text-[11px] text-gray-400">
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block"/>이슈</span>
        <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-300 inline-block"/>주간</span>
      </div>
    </div>
  )
}

// ── 갤러리 대시보드 ───────────────────────────────────────────────────────

function GalleryDashboard({
  list,
  t,
}: {
  list: Awaited<ReturnType<typeof getGalleryList>>
  t: Record<string, string>
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-xs font-medium text-gray-400">
          {tp(t, 'home.dashboard.title', { count: list.length }, '추적 중인 갤러리 {count}개')}
        </h2>
        <Link href="/gallery" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
          {t['common.view_all'] ?? '전체 보기 →'}
        </Link>
      </div>
      <div className="space-y-1.5">
        {list.map(g => (
          <Link key={g.id} href={`/gallery/${g.id}`} className="flex items-center justify-between py-1 hover:bg-gray-50 -mx-1 px-1 rounded transition-colors">
            <span className="text-sm text-gray-800 truncate">{g.name}</span>
            <div className="flex items-center gap-2 shrink-0 ml-2">
              {g.recent_issue_days > 0 ? (
                <span className="text-xs text-amber-600 tabular-nums">
                  {tp(t, 'home.dashboard.recent_issues', { count: g.recent_issue_days }, '4주 {count}일')}
                </span>
              ) : (
                <span className="text-xs text-gray-300">—</span>
              )}
              {g.latest_issue && (
                <span className={`text-xs font-medium tabular-nums ${g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'}`}>
                  {g.latest_issue.score}점
                </span>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

// ── 최근 7일 이슈 ────────────────────────────────────────────────────────

function RecentIssues({
  data,
  t,
}: {
  data: Awaited<ReturnType<typeof getRecentDailyIssues>>
  t: Record<string, string>
}) {
  if (!data.length) return (
    <p className="text-sm text-gray-400 text-center py-6">{t['common.no_data'] ?? '데이터 없음'}</p>
  )

  return (
    <div className="space-y-3">
      {data.map(({ date, issues }) => (
        <div key={date}>
          <Link href={`/daily/${date}`} className="block">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs font-medium text-gray-500">{fmtShort(date)}</span>
              <span className="text-xs text-gray-400 hover:text-gray-600">→</span>
            </div>
            <div className="space-y-1">
              {issues.filter(i => i.has_issue).map(i => (
                <div key={i.gallery_id} className="flex items-center gap-2">
                  <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${i.issue_score >= 7 ? 'bg-red-500' : 'bg-orange-400'}`} />
                  <span className="text-sm text-gray-800 truncate flex-1">{i.gallery_name}</span>
                  {i.temperature_tag && (
                    <span className="text-xs text-gray-400 shrink-0">{i.temperature_tag}</span>
                  )}
                  <span className={`text-xs font-medium tabular-nums shrink-0 ${i.issue_score >= 7 ? 'text-red-600' : 'text-orange-500'}`}>
                    {i.issue_score}점
                  </span>
                </div>
              ))}
            </div>
          </Link>
          <div className="border-b border-gray-100 mt-3" />
        </div>
      ))}
    </div>
  )
}

// ── 최근 주간 요약 ───────────────────────────────────────────────────────

function WeeklySummarySection({
  data,
  t,
}: {
  data: Awaited<ReturnType<typeof getLatestWeeklyOverall>>
  t: Record<string, string>
}) {
  if (!data) return null

  return (
    <section className="space-y-4">
      <div className="flex items-baseline justify-between">
        <div>
          <h2 className="text-sm font-semibold text-gray-900">
            {t['home.weekly_summary.title'] ?? '이번 주 종합 요약'}
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            {fmtShort(data.week_start)} ~ {fmtShort(data.week_end)}
          </p>
        </div>
        <Link href={`/weekly/${data.week_start}`} className="text-xs text-gray-400 hover:text-gray-700 transition-colors">
          {t['common.view_all'] ?? '전체 보기 →'}
        </Link>
      </div>

      {data.ai_summary && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">{data.ai_summary}</p>
        </div>
      )}

      {data.galleries.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {data.galleries.map(g => <WeeklyMiniCard key={g.gallery_id} g={g} t={t} />)}
        </div>
      )}
    </section>
  )
}

function WeeklyMiniCard({ g, t }: { g: WeeklyGallery; t: Record<string, string> }) {
  const kws  = Array.isArray(g.keywords)  ? g.keywords.slice(0, 4)  : []
  const tops = Array.isArray(g.top_posts) ? g.top_posts.slice(0, 2) : []
  const hasCounts = g.daily_counts && Object.keys(g.daily_counts).length > 0
  const hasAI = g.ai_summary && g.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm text-gray-900">{g.gallery_name}</span>
        <span className="text-xs tabular-nums text-gray-400">{g.total_posts}건</span>
      </div>
      {hasCounts && <WeeklyBarChart dailyCounts={g.daily_counts!} />}
      {kws.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {kws.map(([kw]) => (
            <span key={kw} className="text-[11px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">#{kw}</span>
          ))}
        </div>
      )}
      {hasAI && (
        <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">{g.ai_summary}</p>
      )}
      {tops.length > 0 && (
        <div className="space-y-1 pt-1 border-t border-gray-100">
          {tops.map((p, i) => (
            <div key={i} className="flex items-start gap-1.5">
              <span className="text-gray-300 text-[11px] tabular-nums shrink-0">{i+1}</span>
              <a href={p.링크} target="_blank" rel="noopener noreferrer"
                className="text-[11px] text-gray-700 hover:underline line-clamp-1 flex-1">
                {p.제목}
              </a>
              <span className="text-[11px] text-gray-400 tabular-nums shrink-0">댓글 {p.댓글수}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── 홈 페이지 ─────────────────────────────────────────────────────────────

export default async function HomePage() {
  const [t, cal, galleryList, recentIssues, weeklySummary] = await Promise.all([
    getTexts(),
    getCalendarData().catch(() => ({ issue_dates: [] as string[], weekly_dates: [] as string[] })),
    getGalleryList().catch(() => []),
    getRecentDailyIssues(7).catch(() => []),
    getLatestWeeklyOverall().catch(() => null),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="home" />

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-8">

        {/* ① 갤러리 대시보드 */}
        <section>
          <GalleryDashboard list={galleryList} t={t} />
        </section>

        {/* ② 캘린더 + 최근 7일 이슈 */}
        <section className="grid grid-cols-1 lg:grid-cols-[minmax(220px,5fr)_7fr] gap-4 items-start">
          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h2 className="text-xs font-medium text-gray-400 mb-3">
              {t['home.calendar.title'] ?? '캘린더'}
            </h2>
            <MiniCalendar issueDates={cal.issue_dates} weeklyDates={cal.weekly_dates} t={t} />
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-baseline justify-between mb-3">
              <h2 className="text-xs font-medium text-gray-400">
                {t['home.recent_issues.title'] ?? '최근 7일 이내 이슈'}
              </h2>
              <Link href="/daily" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
                {t['common.view_all'] ?? '전체 보기 →'}
              </Link>
            </div>
            <RecentIssues data={recentIssues} t={t} />
          </div>
        </section>

        {/* ③ 최근 주간 리포트 요약 */}
        <WeeklySummarySection data={weeklySummary} t={t} />

      </main>
    </div>
  )
}
