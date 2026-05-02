import Link from 'next/link'
import type { DailyIssue, WeeklyGallery } from '@/types'
import {
  getCalendarData,
  getLatestDailyInfo,
  getLatestWeeklyInfo,
  getDailyByDate,
  getWeeklyByWeek,
} from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'

function fmt(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

// ── 달력 ─────────────────────────────────────────────────────────────────

function GridCalendar({
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

  const issueSet = new Set(issueDates)
  const weeklySet = new Set(weeklyDates)

  const [ty, tm, td] = todayStr.split('-').map(Number)
  const todayDOW = new Date(Date.UTC(ty, tm - 1, td)).getUTCDay()
  const calStart = new Date(Date.UTC(ty, tm - 1, td - todayDOW - 14))

  const toDateStr = (dt: Date) =>
    [
      dt.getUTCFullYear(),
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

  const DAY_LABELS = ['일', '월', '화', '수', '목', '금', '토']

  return (
    <div>
      <div className="grid grid-cols-7 mb-1">
        {DAY_LABELS.map((label, i) => (
          <div
            key={label}
            className={`text-center text-[11px] py-0.5 font-medium ${
              i === 0 ? 'text-red-400' : i === 6 ? 'text-blue-400' : 'text-gray-400'
            }`}
          >
            {label}
          </div>
        ))}
      </div>

      {weeks.map((week, wi) => (
        <div key={wi} className="grid grid-cols-7 mb-0.5">
          {week.map((dateStr, di) => {
            const dayNum = parseInt(dateStr.slice(8), 10)
            const isToday = dateStr === todayStr
            const isFuture = dateStr > todayStr
            const hasIssue = issueSet.has(dateStr)
            const hasWeekly = weeklySet.has(dateStr)
            const isSun = di === 0
            const isSat = di === 6

            const href = !isFuture
              ? hasIssue ? `/daily/${dateStr}` : hasWeekly ? `/weekly/${dateStr}` : null
              : null

            const cell = (
              <div
                className={`flex flex-col items-center py-1 rounded select-none ${
                  isToday ? 'bg-blue-600' : href ? 'hover:bg-gray-100 cursor-pointer' : ''
                }`}
              >
                <span
                  className={`text-xs font-medium leading-none ${
                    isToday
                      ? 'text-white'
                      : isFuture
                        ? 'text-gray-300'
                        : isSun
                          ? 'text-red-500'
                          : isSat
                            ? 'text-blue-500'
                            : 'text-gray-800'
                  }`}
                >
                  {dayNum}
                </span>
                {isToday && (
                  <span className="text-[9px] text-blue-200 leading-none mt-0.5">오늘</span>
                )}
                {!isToday && (
                  <div className="flex gap-px mt-1 h-1.5 items-center">
                    {hasIssue && <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />}
                    {hasWeekly && <span className="w-1.5 h-1.5 rounded-full bg-blue-300 shrink-0" />}
                    {!hasIssue && !hasWeekly && <span className="w-1.5 h-1.5 shrink-0" />}
                  </div>
                )}
              </div>
            )

            return href ? (
              <Link key={dateStr} href={href}>{cell}</Link>
            ) : (
              <div key={dateStr}>{cell}</div>
            )
          })}
        </div>
      ))}

      <div className="flex items-center gap-4 mt-2 pt-2 border-t border-gray-100">
        <span className="flex items-center gap-1.5 text-[11px] text-gray-400">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 inline-block" />
          {t['home.calendar.legend_issue'] ?? '이슈'}
        </span>
        <span className="flex items-center gap-1.5 text-[11px] text-gray-400">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-300 inline-block" />
          {t['home.calendar.legend_weekly'] ?? '주간 리포트'}
        </span>
      </div>
    </div>
  )
}

// ── 일간 이슈 행 ──────────────────────────────────────────────────────────

function IssueRow({ issue, t }: { issue: DailyIssue; t: Record<string, string> }) {
  const isHigh = issue.issue_score >= 7
  const isMid = issue.has_issue && issue.issue_score < 7
  const dotCls = isHigh ? 'bg-red-500' : isMid ? 'bg-orange-400' : 'bg-amber-400'
  const scoreCls = isHigh ? 'text-red-600' : isMid ? 'text-orange-500' : 'text-amber-600'

  return (
    <div className="py-2.5 border-b border-gray-100 last:border-0">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`w-2 h-2 rounded-full shrink-0 ${dotCls}`} />
          <span className="text-sm font-medium text-gray-900 truncate">{issue.gallery_name}</span>
          {issue.is_borderline && !issue.has_issue && (
            <span className="text-xs text-gray-400 shrink-0">
              {t['common.borderline_label'] ?? '경계'}
            </span>
          )}
        </div>
        <span className={`text-sm font-semibold tabular-nums shrink-0 ${scoreCls}`}>
          {issue.issue_score}점
        </span>
      </div>
      {issue.ai_summary && (
        <p className="text-xs text-gray-500 mt-0.5 ml-4 line-clamp-2 leading-relaxed">
          {issue.ai_summary}
        </p>
      )}
    </div>
  )
}

// ── 주간 갤러리 카드 ───────────────────────────────────────────────────────

function WeeklyGalleryCard({ g, t }: { g: WeeklyGallery; t: Record<string, string> }) {
  const kws = Array.isArray(g.keywords) ? g.keywords.slice(0, 5) : []
  const tops = Array.isArray(g.top_posts) ? g.top_posts.slice(0, 3) : []
  const hasCounts = g.daily_counts && Object.keys(g.daily_counts).length > 0
  const hasAI = g.ai_summary && g.ai_summary !== '(주간 게시글 10건 미만 — AI 요약 제외)'

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-medium text-sm text-gray-900">{g.gallery_name}</span>
        <span className="text-sm tabular-nums text-gray-500">
          {t['weekly_detail.total_label'] ?? '총'}{' '}
          <span className="text-gray-900 font-semibold">{g.total_posts}</span>건
        </span>
      </div>

      {hasCounts && <WeeklyBarChart dailyCounts={g.daily_counts!} />}

      {kws.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {kws.map(([kw]) => (
            <span key={kw} className="text-[11px] px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded">
              #{kw}
            </span>
          ))}
        </div>
      )}

      {hasAI && (
        <p className="text-xs text-gray-600 leading-relaxed">{g.ai_summary}</p>
      )}

      {tops.length > 0 && (
        <div className="space-y-1.5 pt-1 border-t border-gray-100">
          {tops.map((p, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className="text-gray-300 text-xs tabular-nums shrink-0 mt-0.5">{i + 1}</span>
              <div className="min-w-0 flex-1">
                <a
                  href={p.링크}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-gray-800 hover:underline line-clamp-1"
                >
                  {p.제목}
                </a>
                <div className="flex gap-2 text-[11px] text-gray-400 mt-0.5 tabular-nums">
                  <span>{tp(t, 'common.comment_count', { count: p.댓글수 }, '댓글 {count}')}</span>
                  <span>{tp(t, 'common.like_count', { count: p.추천수 }, '추천 {count}')}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ── 홈 페이지 ─────────────────────────────────────────────────────────────

export default async function HomePage() {
  const [t, cal, dailyInfo, weeklyInfo] = await Promise.all([
    getTexts(),
    getCalendarData().catch(() => ({ issue_dates: [] as string[], weekly_dates: [] as string[] })),
    getLatestDailyInfo().catch(() => null),
    getLatestWeeklyInfo().catch(() => null),
  ])

  const latestDate = dailyInfo?.date

  const [dailyIssues, weeklyData] = await Promise.all([
    latestDate ? getDailyByDate(latestDate).catch(() => []) : Promise.resolve([]),
    weeklyInfo?.week_start
      ? getWeeklyByWeek(weeklyInfo.week_start).catch(() => null)
      : Promise.resolve(null),
  ])

  const issues = dailyIssues
    .filter(i => i.has_issue || i.is_borderline)
    .sort((a, b) => b.issue_score - a.issue_score)
  const normalCount = dailyIssues.filter(i => !i.has_issue && !i.is_borderline).length

  const weeklyGalleries = weeklyData?.galleries
    ? [...weeklyData.galleries].sort((a, b) => b.total_posts - a.total_posts)
    : []

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="home" />

      <main className="max-w-6xl mx-auto px-4 py-6 space-y-6">

        {/* 상단: 달력(좌) + 일간 이슈(우) */}
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(220px,5fr)_7fr] gap-4 items-start">

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <h2 className="text-xs text-gray-400 font-medium mb-3">
              {t['home.calendar.title'] ?? '캘린더'}
            </h2>
            <GridCalendar issueDates={cal.issue_dates} weeklyDates={cal.weekly_dates} t={t} />
          </div>

          <div className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <h2 className="text-xs text-gray-400 font-medium">
                  {latestDate
                    ? `${fmt(latestDate)} ${t['home.daily.panel_title'] ?? '일간 이슈'}`
                    : (t['home.daily.panel_title'] ?? '일간 이슈')}
                </h2>
                {issues.filter(i => i.has_issue).length > 0 && (
                  <p className="text-xs text-gray-500 mt-0.5">
                    {tp(t, 'home.daily.issue_detected',
                      { count: issues.filter(i => i.has_issue).length },
                      '이슈 {count}개 갤러리 감지')}
                  </p>
                )}
              </div>
              {latestDate && (
                <Link
                  href={`/daily/${latestDate}`}
                  className="text-xs text-gray-400 hover:text-gray-700 transition-colors shrink-0"
                >
                  {t['common.view_all'] ?? '전체 보기 →'}
                </Link>
              )}
            </div>

            {issues.length > 0 ? (
              <>
                <div>
                  {issues.map(i => <IssueRow key={i.gallery_id} issue={i} t={t} />)}
                </div>
                {normalCount > 0 && (
                  <p className="text-xs text-gray-400 mt-2">
                    {tp(t, 'home.daily.normal_count', { count: normalCount }, '그 외 {count}개 갤러리 정상')}
                  </p>
                )}
              </>
            ) : (
              <div className="py-8 text-center">
                <p className="text-sm text-gray-400">
                  {latestDate
                    ? (t['home.daily.no_issue'] ?? '이슈 갤러리 없음')
                    : (t['common.no_data'] ?? '데이터 없음')}
                </p>
                {normalCount > 0 && (
                  <p className="text-xs text-gray-400 mt-1">
                    {tp(t, 'home.daily.all_normal', { count: normalCount }, '전체 {count}개 갤러리 정상 운영 중')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 주간 갤러리 동향 */}
        {weeklyGalleries.length > 0 && weeklyInfo && (
          <section>
            <div className="flex items-baseline justify-between mb-3">
              <div>
                <h2 className="text-sm font-semibold text-gray-900">
                  {t['home.weekly.title'] ?? '이번 주 갤러리 동향'}
                </h2>
                <p className="text-xs text-gray-400 mt-0.5">
                  {fmt(weeklyInfo.week_start)} ~ {fmt(weeklyInfo.week_end ?? '')} ·{' '}
                  {tp(t, 'common.gallery_count', { count: weeklyGalleries.length }, '{count}개 갤러리')}
                </p>
              </div>
              <Link
                href={`/weekly/${weeklyInfo.week_start}`}
                className="text-xs text-gray-400 hover:text-gray-700 transition-colors"
              >
                {t['common.view_all'] ?? '전체 보기 →'}
              </Link>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {weeklyGalleries.map(g => (
                <WeeklyGalleryCard key={g.gallery_id} g={g} t={t} />
              ))}
            </div>
          </section>
        )}

      </main>
    </div>
  )
}
