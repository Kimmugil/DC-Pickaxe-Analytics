import Link from 'next/link'
import { notFound } from 'next/navigation'
import { feedbackFor, galleries, galleryDays, galleryInfo, galleryMonthReports, monthDays, periodReports } from '@/lib/queries'
import { LEVEL_RANK, levelOf, shortName } from '@/lib/level'
import { getTexts, T } from '@/lib/texts'
import { Bars } from '@/components/Bars'
import { MonthCalendar } from '@/components/MonthCalendar'
import { Card, Chip, Empty, Legend, PageHeader, Section, StatusPill, Tile } from '@/components/kit'
import { DayCard, PeriodReport } from '@/components/report'
import { Thumb } from '@/components/Thumb'
import { isAdmin } from '@/lib/auth'

export const dynamic = 'force-dynamic'

const TYPE: Record<string, string> = { major: '일반 갤러리', minor: '마이너 갤러리', mini: '미니 갤러리' }
const PREFIX: Record<string, string> = { minor: 'mgallery/board', major: 'board', mini: 'mini/board' }

function shift(month: string, d: number) {
  const [y, m] = month.split('-').map(Number)
  const dt = new Date(Date.UTC(y, m - 1 + d, 1))
  return `${dt.getUTCFullYear()}-${String(dt.getUTCMonth() + 1).padStart(2, '0')}`
}

/** 앵커 이동 시 상단 메뉴에 가리지 않게 하고, 이동해 온 카드는 배경과 테두리가 바뀐다(globals.css의 .anchor:target) */
function Anchor({ id, children }: { id: string; children: React.ReactNode }) {
  return <div id={id} className="anchor">{children}</div>
}

export default async function GalleryDetail({ params, searchParams }: {
  params: Promise<{ id: string }>; searchParams: Promise<{ tab?: string; month?: string }>
}) {
  const { id } = await params
  const sp = await searchParams
  const [g, t, all] = await Promise.all([galleryInfo(id), getTexts(), galleries()])
  if (!g) notFound()
  const admin = await isAdmin()
  const tab = (['weekly', 'monthly'] as string[]).includes(sp.tab ?? '') ? (sp.tab as 'weekly' | 'monthly') : 'daily'

  const days = await galleryDays(id, 120)
  const withLevel = days.map(d => ({ ...d, level: levelOf({ ...d, extra: d.modern ? {} : null }) }))
  const last = withLevel.at(-1)
  const recent28 = withLevel.slice(-28)
  const issue28 = recent28.filter(d => LEVEL_RANK[d.level] >= 2).length
  const avg28 = recent28.length ? Math.round(recent28.reduce((s, d) => s + (d.post_count || 0), 0) / recent28.length) : 0
  const month = /^\d{4}-\d{2}$/.test(sp.month ?? '') ? sp.month! : (last?.day ?? new Date().toISOString()).slice(0, 7)
  const tabQuery = tab === 'daily' ? '' : `?tab=${tab}`
  const active = all.filter(x => x.is_active)

  return (
    <div>
      {/* 지금 어디에 있는지: 빵부스러기 + 갤러리 전환 칩 */}
      <nav aria-label="현재 위치" className="mb-3 flex flex-wrap items-center gap-x-2 text-sm text-slate-400">
        <Link href="/" className="hover:text-slate-700">홈</Link><span>›</span>
        <Link href="/gallery" className="hover:text-slate-700">갤러리</Link><span>›</span>
        <span className="font-semibold text-slate-800">{g.name}</span>
      </nav>
      <div className="mb-5 flex flex-wrap items-center gap-1.5">
        {active.map(x => (
          <Link key={x.gallery_id} href={`/gallery/${x.gallery_id}${tabQuery}`}
                className={`rounded-full px-3 py-1 text-sm transition-colors ${x.gallery_id === id ? 'bg-slate-900 font-semibold text-white' : 'border border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}`}>
            {shortName(x)}
          </Link>
        ))}
      </div>

      <div className="mb-6 flex items-start gap-4">
        <Thumb id={id} name={g.name} has={g.has_thumb} className="h-16 w-20 shrink-0 sm:h-20 sm:w-28" />
        <div className="min-w-0 flex-1">
          <PageHeader title={g.name}
            sub={<span className="flex flex-wrap items-center gap-2"><Chip>{TYPE[g.gallery_type] ?? g.gallery_type}</Chip>{!g.is_active && <Chip tone="amber">수집 중단</Chip>}
              <a href={`https://gall.dcinside.com/${PREFIX[g.gallery_type]}/lists/?id=${g.gallery_id}`} target="_blank" rel="noreferrer" className="text-xs text-slate-400 hover:underline">디시 갤러리 열기 ↗</a></span>} />
        </div>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="rounded-xl border border-slate-200 bg-white px-4 py-3"><div className="text-xs text-slate-500">현재 온도</div>
          <div className="mt-1.5">{last ? <StatusPill level={last.level} /> : <span className="text-slate-400">-</span>}</div><div className="mt-1 text-xs text-slate-400">{last ? `${last.day} 기준` : '분석 기록 없음'}</div></div>
        <Tile label={last ? `${last.day.slice(5).replace('-', '월 ')}일 게시량` : '최근 분석일 게시량'} value={`${last?.post_count ?? 0}건`} sub={`최근 28일 하루 평균 ${avg28}건`} />
        <Tile label="최근 28일 이슈" value={`${issue28}일`} tone={issue28 ? 'danger' : 'default'} sub="이슈 이상 온도였던 날" />
        <Tile label="분석 기록" value={`${days.length}일`} sub="최근 120일 중" />
      </div>

      {/* 탭: 회색 바 안에서 선택된 것이 흰 판으로 올라온 형태 — 누를 수 있는 것임이 보이면서 버튼처럼 무겁지 않게 */}
      <div role="tablist" className="mb-6 inline-flex rounded-lg bg-slate-100 p-1">
        {(['daily', 'weekly', 'monthly'] as const).map(k => (
          <Link key={k} href={`/gallery/${id}${k === 'daily' ? '' : `?tab=${k}`}`} role="tab" aria-selected={tab === k}
                className={`rounded-md px-4 py-1.5 text-sm transition-colors ${tab === k ? 'bg-white font-semibold text-slate-900 shadow-sm' : 'text-slate-500 hover:bg-white/60 hover:text-slate-800'}`}>
            {T(t, `gallery.tab.${k}`)}
          </Link>
        ))}
      </div>

      {tab === 'daily' && <DailyTab id={id} g={g} month={month} days={withLevel} admin={admin} emptyText={T(t, 'gallery.empty.month', { month })} />}
      {tab === 'weekly' && <PeriodTab id={id} kind="weekly" />}
      {tab === 'monthly' && <PeriodTab id={id} kind="monthly" />}
    </div>
  )
}

async function DailyTab({ id, g, month, days, emptyText, admin }: { admin: boolean; id: string; g: { gallery_id: string; name: string; short_name: string | null }; month: string; days: Awaited<ReturnType<typeof galleryDays>>; emptyText: string }) {
  const [marks, reports] = await Promise.all([monthDays(month), galleryMonthReports(id, month)])
  const cards = reports.map(r => ({ r, l: levelOf(r) })).filter(x => LEVEL_RANK[x.l] >= 1)
  const fb = Object.fromEntries(await Promise.all(cards.map(async x => [x.r.id, await feedbackFor(x.r.id)])))
  const q = (m: string) => `/gallery/${id}?month=${m}`
  return (
    <>
      <Section title="추이" hint="최근 120일 일별 게시량 · 막대 색이 그날의 온도">
        <Card className="p-4"><Bars days={days} /></Card>
      </Section>

      <Section title="캘린더" hint="칩이나 날짜를 누르면 아래에서 해당 리포트 카드가 강조됩니다"
        right={<span className="flex items-center gap-2">
          <Link href={q(shift(month, -1))} className="btn-ghost" aria-label="이전 달">‹</Link>
          <span className="w-20 text-center text-sm font-semibold">{month}</span>
          <Link href={q(shift(month, 1))} className="btn-ghost" aria-label="다음 달">›</Link></span>}>
        <Legend className="mb-3" />
        <MonthCalendar month={month} marks={marks} galleries={[g]} onlyGallery={id} dateHref={d => `/gallery/${id}?month=${month}#d-${d}`} />
      </Section>

      <Section title={`${month} 리포트`} hint="이슈와 주목이었던 날만 보여줍니다. 요약은 이슈였던 날에만 만듭니다">
        {cards.length ? (
          <div className="space-y-4">
            {cards.map(x => <Anchor key={x.r.id} id={`d-${x.r.start}`}><DayCard r={x.r} level={x.l} feedback={fb[x.r.id]} admin={admin} /></Anchor>)}
          </div>
        ) : <Empty>{emptyText}</Empty>}
      </Section>
    </>
  )
}

async function PeriodTab({ id, kind }: { id: string; kind: 'weekly' | 'monthly' }) {
  const list = await periodReports(kind === 'weekly' ? 'week' : 'month', id)
  const label = kind === 'weekly' ? '주간' : '월간'
  const title = (r: (typeof list)[number]) => (kind === 'weekly' ? `${r.start} ~ ${r.end}` : r.start.slice(0, 7))
  const anchor = (r: (typeof list)[number]) => (kind === 'weekly' ? `w-${r.start}` : `m-${r.start.slice(0, 7)}`)
  return (
    <Section title={`${label} 리포트`} hint={kind === 'weekly' ? '월요일~일요일 · 이 갤러리에서 가장 화제가 된 것' : '한 달 동안 이 갤러리에서 가장 화제가 된 것'}>
      {list.length ? (
        <div className="space-y-4">
          {list.map((r, i) => (
            <Anchor key={r.id} id={anchor(r)}>
              {i < 2 ? (
                <><div className="mb-1.5 text-sm font-semibold text-slate-700">{title(r)}</div><PeriodReport r={r} galleryId={id} kind={label} /></>
              ) : (
                <details className="group rounded-xl border border-slate-200 bg-white">
                  <summary className="flex cursor-pointer list-none items-baseline gap-3 px-5 py-3 hover:bg-slate-50">
                    <span className="text-slate-400 transition-transform group-open:rotate-90">›</span>
                    <span className="text-sm font-semibold text-slate-700">{title(r)}</span>
                    <span className="min-w-0 flex-1 truncate text-sm text-slate-500">{r.headline ?? '(요약 없음)'}</span>
                  </summary>
                  <div className="p-3"><PeriodReport r={r} galleryId={id} kind={label} /></div>
                </details>
              )}
            </Anchor>
          ))}
        </div>
      ) : <Empty>아직 {label} 리포트가 없습니다.</Empty>}
    </Section>
  )
}
