import Link from 'next/link'
import { LEVEL_RANK, dayHref } from '@/lib/level'
import { Card, Empty, StatusPill } from './kit'
import { withLevel, type Mark } from './MonthCalendar'

/** 캘린더에서 고른 날의 요약: 평소와 달랐던 갤러리를 온도 순으로. 각 줄을 누르면 그 갤러리의 리포트 카드로 이동한다. */
export function DayPanel({ day, marks, names }: { day: string; marks: Mark[]; names: Record<string, string> }) {
  const rows = marks.filter(m => m.day === day).map(withLevel).sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level] || b.issue_score - a.issue_score)
  const wd = ['일', '월', '화', '수', '목', '금', '토'][new Date(`${day}T00:00:00Z`).getUTCDay()]
  return (
    <Card>
      <div className="flex items-baseline gap-2 border-b border-slate-100 px-4 py-2.5">
        <span className="font-semibold text-slate-900">{day} ({wd})</span>
        <span className="text-xs text-slate-500">{rows.length ? `평소와 달랐던 갤러리 ${rows.length}곳` : '모든 갤러리가 평소 수준이었습니다'}</span>
      </div>
      {rows.length ? (
        <ul className="divide-y divide-slate-100">
          {rows.map(r => (
            <li key={r.gallery_id}>
              <Link href={dayHref(r.gallery_id, day)} className="flex flex-col gap-1 px-4 py-3 text-sm hover:bg-slate-50 sm:flex-row sm:items-center sm:gap-x-3">
                <span className="flex items-center gap-2 sm:contents"><StatusPill level={r.level} className="w-[4.5rem] justify-center" />
                <span className="font-semibold text-slate-900 sm:w-36 sm:shrink-0">{names[r.gallery_id] ?? r.gallery_id}</span></span>
                <span className="min-w-0 flex-1 text-slate-600">{r.headline ?? r.summary ?? '(요약 없음)'}</span>
                <span className="text-xs text-indigo-700">리포트 보기 →</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : <div className="px-4 py-6 text-center text-sm text-slate-400">표시할 이슈가 없습니다.</div>}
    </Card>
  )
}
export { Empty }
