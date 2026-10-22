import Link from 'next/link'
import { galleries, monthDays, statusBoard } from '@/lib/queries'
import { LEVEL_META, LEVEL_RANK, dayHref, shortName, type Level } from '@/lib/level'
import { getTexts, T } from '@/lib/texts'
import { Card, Legend, PageHeader, Section, Spark, StatusPill } from '@/components/kit'
import { MonthCalendar } from '@/components/MonthCalendar'
import { DayPanel } from '@/components/DayPanel'
import { factsOf } from '@/components/report'
import { Thumb } from '@/components/Thumb'

export const dynamic = 'force-dynamic'

function shift(month: string, d: number) {
  const [y, m] = month.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1 + d, 1))
  return `${dt.getUTCFullYear()}-${String(dt.getUTCMonth() + 1).padStart(2, '0')}`
}

export default async function Home({ searchParams }: { searchParams: Promise<{ month?: string; date?: string }> }) {
  const sp = await searchParams
  const [t, board, gals] = await Promise.all([getTexts(), statusBoard(7), galleries()])
  const latest = board.dates.at(-1) ?? ''
  const date = /^\d{4}-\d{2}-\d{2}$/.test(sp.date ?? '') ? sp.date! : latest
  const month = /^\d{4}-\d{2}$/.test(sp.month ?? '') ? sp.month! : date.slice(0, 7) || new Date().toISOString().slice(0, 7)
  const marks = await monthDays(month)
  const panelMarks = date.startsWith(month) ? marks : await monthDays(date.slice(0, 7))
  const names = Object.fromEntries(gals.map(g => [g.gallery_id, g.name]))
  const active = gals.filter(g => g.is_active)
  const q = (m: string) => `/?month=${m}`

  const groups: { level: Level; rows: typeof board.rows }[] = [
    { level: 'issue', rows: board.rows.filter(r => LEVEL_RANK[r.level] >= 2) },
    { level: 'watch', rows: board.rows.filter(r => r.level === 'watch') },
    { level: 'normal', rows: board.rows.filter(r => r.level === 'normal') },
  ]
  const rising = board.rows.flatMap(r => (r.latest?.extra?.rising ?? []).map((x: [string, number, number]) => ({ g: r.name, id: r.gallery_id, w: x[0], c: x[1] })))
    .sort((a, b) => b.c - a.c).slice(0, 8)

  return (
    <div>
      <PageHeader title={T(t, 'nav.title')}
        sub={latest ? <>분석 기준일 <b className="text-slate-700">{latest}</b> · 추적 갤러리 {active.length}개</> : '아직 분석된 날이 없습니다'} />

      {/* 오늘의 온도: 누르면 해당 갤러리의 그날 리포트 카드로 이동 */}
      <div className="mb-8 grid gap-3 sm:grid-cols-3">
        {groups.map(({ level, rows }) => (
          <div key={level} className="rounded-xl border border-slate-200 bg-white px-4 py-3">
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <i className={`h-2.5 w-2.5 rounded-full ${LEVEL_META[level].dot}`} />
              {level === 'issue' ? '이슈' : LEVEL_META[level].label}
              <span className="text-slate-400">· {level === 'issue' ? '평소와 확연히 달랐던' : LEVEL_META[level].help}</span>
            </div>
            <div className="mt-1 text-2xl font-bold tracking-tight text-slate-900">{rows.length}곳</div>
            <div className="mt-2 flex min-h-7 flex-wrap gap-1.5">
              {rows.map(r => (
                <Link key={r.gallery_id} href={level === 'normal' ? `/gallery/${r.gallery_id}` : dayHref(r.gallery_id, latest)}
                      className={`rounded-md px-2 py-0.5 text-xs font-medium hover:opacity-80 ${LEVEL_META[r.level].chip}`}>{shortName(r)}</Link>
              ))}
              {!rows.length && <span className="text-xs text-slate-300">없음</span>}
            </div>
          </div>
        ))}
      </div>

      <Section title={T(t, 'home.calendar.title')} hint={T(t, 'home.calendar.hint')}
        right={
          <span className="flex items-center gap-2">
            <Link href={q(shift(month, -1))} className="btn-ghost" aria-label="이전 달">‹</Link>
            <span className="w-20 text-center text-sm font-semibold">{month}</span>
            <Link href={q(shift(month, 1))} className="btn-ghost" aria-label="다음 달">›</Link>
          </span>}>
        <Legend className="mb-3" />
        <MonthCalendar month={month} marks={marks} galleries={gals} selected={date} last={latest}
          dateHref={d => `/?month=${month}&date=${d}`} />
        {date && <div className="mt-4"><DayPanel day={date} marks={panelMarks} names={names} /></div>}
      </Section>

      <Section title={T(t, 'home.status.title')} hint={T(t, 'home.status.hint')} right={<Link href="/gallery" className="text-slate-500 hover:underline">전체 보기 →</Link>}>
        <Card>
          <ul className="divide-y divide-slate-100">
            {board.rows.map(r => {
              const f = r.latest ? factsOf(r.latest) : null
              return (
                <li key={r.gallery_id}>
                  <Link href={`/gallery/${r.gallery_id}`} className="grid grid-cols-[3rem_5.5rem_1fr_auto] items-center gap-3 px-4 py-3 hover:bg-slate-50 sm:grid-cols-[3rem_5.5rem_11rem_1fr_auto]">
                    <Thumb id={r.gallery_id} name={r.name} has={r.has_thumb} className="h-9 w-12 !rounded-lg !text-sm" />
                    <StatusPill level={r.level} className="justify-self-start" />
                    <span className="truncate font-medium text-slate-900">{r.name}</span>
                    <span className="hidden truncate text-sm text-slate-500 sm:block">
                      {r.latest ? <>{r.latest.post_count}건{f?.baseline ? <span className="text-slate-400"> · 평소 {Math.round(f.baseline)}건</span> : null}
                        {r.level !== 'normal' && r.latest.headline ? <span className="text-slate-700"> — {r.latest.headline}</span> : null}</> : '분석 기록 없음'}
                    </span>
                    <Spark days={r.days} height={28} barWidth={9} />
                  </Link>
                </li>
              )
            })}
          </ul>
        </Card>
      </Section>

      {!!rising.length && (
        <Section title={T(t, 'home.rising.title')} hint={`${latest} 기준`}>
          <div className="flex flex-wrap gap-2">
            {rising.map((x, i) => (
              <Link key={i} href={`/gallery/${x.id}`} className="rounded-lg bg-indigo-50 px-3 py-1.5 text-sm text-indigo-900 hover:bg-indigo-100">
                <b>{x.w}</b> <span className="text-xs text-indigo-600">{x.g} · {x.c}회</span>
              </Link>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}
