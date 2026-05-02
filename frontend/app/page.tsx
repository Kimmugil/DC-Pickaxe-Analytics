import Link from 'next/link'
import type { WeeklyGallery } from '@/types'
import {
  getCalendarData,
  getGalleryList,
  getLatestWeeklyOverall,
} from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { WeeklyBarChart } from '@/components/WeeklyBarChart'
import { CalendarClient } from '@/components/CalendarClient'

function fmtShort(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
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
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-6 gap-y-1">
        {list.map(g => (
          <Link
            key={g.id}
            href={`/gallery/${g.id}`}
            className="flex items-center justify-between py-1 hover:bg-gray-50 -mx-1 px-1 rounded transition-colors"
          >
            <span className="text-sm text-gray-800 truncate">{g.name}</span>
            <div className="flex items-center gap-2 shrink-0 ml-2">
              {g.recent_issue_days > 0 ? (
                <span className="text-xs text-amber-600 tabular-nums">
                  이슈빈도 {g.recent_issue_days}일/4주
                </span>
              ) : (
                <span className="text-xs text-gray-300">—</span>
              )}
              {g.latest_issue && (
                <span className={`text-xs font-medium tabular-nums ${g.latest_issue.score >= 7 ? 'text-red-500' : 'text-orange-500'}`}>
                  최근 {g.latest_issue.score}점
                </span>
              )}
            </div>
          </Link>
        ))}
      </div>
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
  const [t, cal, galleryList, weeklySummary] = await Promise.all([
    getTexts(),
    getCalendarData().catch(() => ({ issuesByDate: {} as Record<string, { id: string; name: string; score: number }[]>, weeklyDates: [] as string[] })),
    getGalleryList().catch(() => []),
    getLatestWeeklyOverall().catch(() => null),
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="home" />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-8">

        {/* ① 갤러리 대시보드 */}
        <section>
          <GalleryDashboard list={galleryList} t={t} />
        </section>

        {/* ② 이슈 캘린더 */}
        <section className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-baseline justify-between mb-3">
            <h2 className="text-xs font-medium text-gray-400">
              {t['home.calendar.title'] ?? '이슈 캘린더'}
            </h2>
            <Link href="/daily" className="text-xs text-gray-400 hover:text-gray-600 transition-colors">
              {t['common.view_all'] ?? '전체 보기 →'}
            </Link>
          </div>
          <CalendarClient issuesByDate={cal.issuesByDate} weeklyDates={cal.weeklyDates} />
        </section>

        {/* ③ 최근 주간 리포트 요약 */}
        <WeeklySummarySection data={weeklySummary} t={t} />

      </main>
    </div>
  )
}
