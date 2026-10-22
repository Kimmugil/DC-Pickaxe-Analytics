import Link from 'next/link'
import { LEVEL_META, LEVEL_RANK, dayHref, levelOf, shortName, type Level } from '@/lib/level'

export type Mark = { day: string; gallery_id: string; has_issue: boolean; is_borderline: boolean; issue_score: number; headline: string | null; summary?: string | null; modern: boolean }
type G = { gallery_id: string; name: string; short_name?: string | null }

export function withLevel(m: Mark): Mark & { level: Level } {
  return { ...m, level: levelOf({ ...m, extra: m.modern ? {} : null }) }
}

/**
 * 월 달력. 칸마다 그날 평소와 달랐던 갤러리를 '약칭 + 온도 색'으로 보여준다.
 * - 약칭을 누르면 그 갤러리의 그날 리포트 카드로 바로 이동
 * - 날짜 숫자를 누르면 dateHref(day)로 이동 (홈에서는 그날 요약 패널)
 * - 좁은 화면에서는 색 점만 보이고, 자세한 건 날짜를 눌러 확인
 */
export function MonthCalendar({ month, marks, galleries, selected, last, dateHref, onlyGallery }: {
  month: string; marks: Mark[]; galleries: G[]; selected?: string; last?: string
  dateHref: (day: string) => string; onlyGallery?: string   // onlyGallery: 한 갤러리 화면 — 약칭 대신 온도 이름을 칩에 표시
}) {
  const [y, m] = month.split('-').map(Number)
  const lead = new Date(Date.UTC(y, m - 1, 1)).getUTCDay()
  const dim = new Date(Date.UTC(y, m, 0)).getUTCDate()
  const gmap = new Map(galleries.map(g => [g.gallery_id, g]))
  const byDay = new Map<string, (Mark & { level: Level })[]>()
  for (const k of marks) {
    if (onlyGallery && k.gallery_id !== onlyGallery) continue
    byDay.set(k.day, [...(byDay.get(k.day) ?? []), withLevel(k)])
  }
  const cells: (number | null)[] = [...Array(lead).fill(null), ...Array.from({ length: dim }, (_, i) => i + 1)]
  while (cells.length % 7) cells.push(null)
  return (
    <div className="grid grid-cols-7 gap-px overflow-hidden rounded-xl border border-slate-200 bg-slate-200">
      {['일', '월', '화', '수', '목', '금', '토'].map((d, i) => (
        <div key={d} className={`bg-slate-50 py-1.5 text-center text-xs ${i === 0 ? 'text-rose-400' : 'text-slate-500'}`}>{d}</div>
      ))}
      {cells.map((d, i) => {
        if (!d) return <div key={i} className="min-h-[4.5rem] bg-slate-50/60 sm:min-h-[6.5rem]" />
        const key = `${month}-${String(d).padStart(2, '0')}`
        const list = (byDay.get(key) ?? []).sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level])
        const top = list[0]?.level
        return (
          <div key={i} className={`bg-white p-1 sm:p-1.5 min-h-[4.5rem] sm:min-h-[6.5rem] ${key === selected ? 'ring-2 ring-inset ring-slate-900' : ''}`}>
            <Link href={dateHref(key)} title="이 날 요약 보기"
                  className={`inline-flex h-6 min-w-6 items-center justify-center rounded-full px-1 text-xs hover:bg-slate-100 ${list.length ? 'font-bold text-slate-900' : 'text-slate-400'} ${key === last ? 'underline decoration-slate-400 underline-offset-4' : ''}`}>{d}</Link>
            {/* 넓은 화면: 약칭 칩 */}
            <div className="mt-1 hidden flex-col gap-0.5 sm:flex">
              {list.map(x => {
                const g = gmap.get(x.gallery_id)
                return (
                  <Link key={x.gallery_id} href={dayHref(x.gallery_id, x.day)} title={`${g?.name ?? x.gallery_id} · ${LEVEL_META[x.level].label}${x.headline ? ' — ' + x.headline : ''}`}
                        className={`truncate rounded px-1.5 py-px text-[11px] font-medium leading-4 hover:opacity-80 ${LEVEL_META[x.level].chip}`}>
                    {onlyGallery ? LEVEL_META[x.level].label : g ? shortName(g) : x.gallery_id}
                  </Link>
                )
              })}
            </div>
            {/* 좁은 화면: 색 점 */}
            {list.length > 0 && <div className="mt-1 flex flex-wrap gap-0.5 sm:hidden">{list.map(x => <i key={x.gallery_id} className={`h-2 w-2 rounded-full ${LEVEL_META[x.level].dot}`} />)}</div>}
            {!list.length && top === undefined && null}
          </div>
        )
      })}
    </div>
  )
}
