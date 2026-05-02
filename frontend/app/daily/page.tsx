import Link from 'next/link'
import { getDailyIssueList } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'

function fmtFull(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

// ── 갤러리 배지 캘린더 ────────────────────────────────────────────────────

function BadgeCalendar({
  issueMap,
  t,
}: {
  issueMap: Map<string, { id: string; name: string; score: number }[]>
  t: Record<string, string>
}) {
  const now = new Date()
  const todayStr = [
    now.getUTCFullYear(),
    String(now.getUTCMonth() + 1).padStart(2, '0'),
    String(now.getUTCDate()).padStart(2, '0'),
  ].join('-')

  const [ty, tm, td] = todayStr.split('-').map(Number)
  const todayDOW = new Date(Date.UTC(ty, tm - 1, td)).getUTCDay()
  // Show 6 weeks (current + 5 prior)
  const calStart = new Date(Date.UTC(ty, tm - 1, td - todayDOW - 28))

  const toDateStr = (dt: Date) =>
    [dt.getUTCFullYear(),
     String(dt.getUTCMonth() + 1).padStart(2, '0'),
     String(dt.getUTCDate()).padStart(2, '0'),
    ].join('-')

  const weeks: string[][] = Array.from({ length: 6 }, (_, w) =>
    Array.from({ length: 7 }, (_, d) => {
      const dt = new Date(calStart)
      dt.setUTCDate(calStart.getUTCDate() + w * 7 + d)
      return toDateStr(dt)
    }),
  )

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      <div className="grid grid-cols-7 border-b border-gray-100">
        {['일','월','화','수','목','금','토'].map((label, i) => (
          <div key={label} className={`text-center text-xs py-2 font-medium ${i===0?'text-red-400':i===6?'text-blue-400':'text-gray-400'}`}>
            {label}
          </div>
        ))}
      </div>

      {weeks.map((week, wi) => (
        <div key={wi} className="grid grid-cols-7 border-b border-gray-100 last:border-0">
          {week.map((dateStr, di) => {
            const dayNum    = parseInt(dateStr.slice(8), 10)
            const isToday   = dateStr === todayStr
            const isFuture  = dateStr > todayStr
            const galleries = issueMap.get(dateStr) ?? []
            const hasIssue  = galleries.length > 0
            const isSun = di === 0, isSat = di === 6

            return (
              <div
                key={dateStr}
                className={`min-h-[70px] p-1 border-r border-gray-100 last:border-0 ${isToday ? 'bg-blue-50' : ''}`}
              >
                <div className={`text-[11px] font-medium mb-1 ${
                  isToday ? 'text-blue-600' : isFuture ? 'text-gray-300' : isSun ? 'text-red-400' : isSat ? 'text-blue-400' : 'text-gray-500'
                }`}>
                  {dayNum}
                  {isToday && <span className="ml-1 text-blue-400 font-normal">오늘</span>}
                </div>

                {hasIssue && (
                  <Link href={`/daily/${dateStr}`} className="flex flex-col gap-0.5">
                    {galleries.slice(0, 3).map(g => (
                      <span
                        key={g.id}
                        className={`block text-[10px] leading-tight px-1 py-0.5 rounded truncate font-medium ${
                          g.score >= 7 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'
                        }`}
                      >
                        {g.name}
                      </span>
                    ))}
                    {galleries.length > 3 && (
                      <span className="text-[10px] text-gray-400 px-1">
                        +{galleries.length - 3}
                      </span>
                    )}
                  </Link>
                )}
              </div>
            )
          })}
        </div>
      ))}
    </div>
  )
}

// ── 일간 이슈 미니 카드 ───────────────────────────────────────────────────

function IssueMiniCard({
  item,
  t,
}: {
  item: Awaited<ReturnType<typeof getDailyIssueList>>[number]
  t: Record<string, string>
}) {
  const topGalleries = item.galleries.filter(g => g.has_issue).slice(0, 3)
  const hasHigh = item.max_score >= 7

  return (
    <Link
      href={`/daily/${item.date}`}
      className="bg-white border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors group flex flex-col gap-2"
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-sm font-semibold text-gray-900">{fmtFull(item.date)}</span>
        <span className={`text-xs font-medium tabular-nums shrink-0 ${hasHigh ? 'text-red-600' : 'text-orange-500'}`}>
          {tp(t, 'common.issue_count', { count: item.issue_count }, '{count}개 이슈')}
        </span>
      </div>

      <div className="flex flex-wrap gap-1">
        {topGalleries.map(g => (
          <span
            key={g.id}
            className={`text-[11px] font-medium px-1.5 py-0.5 rounded ${g.score >= 7 ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}`}
          >
            {g.name} {g.score}점
          </span>
        ))}
        {item.issue_count > 3 && (
          <span className="text-[11px] text-gray-400 px-1 py-0.5">+{item.issue_count - 3}</span>
        )}
      </div>

      {item.borderline_count > 0 && (
        <p className="text-xs text-gray-400">
          {tp(t, 'common.borderline_count', { count: item.borderline_count }, '경계 {count}개')}
        </p>
      )}

      <div className="flex items-center justify-between pt-1.5 border-t border-gray-100 mt-auto">
        <span className="text-[11px] text-gray-400">{item.date}</span>
        <span className="text-gray-300 group-hover:text-gray-500 text-sm transition-colors">→</span>
      </div>
    </Link>
  )
}

// ── 일간 이슈 페이지 ─────────────────────────────────────────────────────

export default async function DailyListPage() {
  const [t, list] = await Promise.all([
    getTexts(),
    getDailyIssueList().catch(() => [] as Awaited<ReturnType<typeof getDailyIssueList>>),
  ])

  // 캘린더용 맵: date → galleries
  const issueMap = new Map<string, { id: string; name: string; score: number }[]>()
  for (const item of list) {
    issueMap.set(item.date, item.galleries.filter(g => g.has_issue))
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav active="daily" />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">

        {/* 갤러리 배지 캘린더 */}
        <section>
          <BadgeCalendar issueMap={issueMap} t={t} />
        </section>

        {/* 카드 보드 */}
        {list.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-10">
            {t['common.no_data'] ?? '데이터 없음'}
          </p>
        ) : (
          <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {list.map(item => (
              <IssueMiniCard key={item.date} item={item} t={t} />
            ))}
          </section>
        )}

      </main>
    </div>
  )
}
