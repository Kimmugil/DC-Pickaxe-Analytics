import Link from 'next/link'
import { galleries, statusBoard } from '@/lib/queries'
import { getTexts, T, tx } from '@/lib/texts'
import { Card, Chip, Legend, PageHeader, Section, Spark, StatusPill } from '@/components/kit'
import { dayHref } from '@/lib/level'
import { factsOf } from '@/components/report'
import { Thumb } from '@/components/Thumb'

export const dynamic = 'force-dynamic'

export default async function GalleryList() {
  const [gals, board, t] = await Promise.all([galleries(), statusBoard(7), getTexts()])
  const inactive = gals.filter(g => !g.is_active)
  return (
    <div>
      <PageHeader title={T(t, 'gallery.list.title')} sub={T(t, 'gallery.list.sub', { count: board.rows.length })} />
      <Legend className="mb-4" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {board.rows.map(r => {
          const f = r.latest ? factsOf(r.latest) : null
          return (
            <Link key={r.gallery_id} href={`/gallery/${r.gallery_id}`} className="block">
              <Card level={r.level === 'normal' ? undefined : r.level} className="h-full overflow-hidden transition-shadow hover:shadow-md">
                <Thumb id={r.gallery_id} name={r.name} has={r.has_thumb} className="h-32 w-full !rounded-none !ring-0 sm:h-40" />
                <div className="px-5 py-4">
                <div className="flex items-center gap-2">
                  <StatusPill level={r.level} />
                  <span className="text-lg font-bold text-slate-900">{r.name}</span>
                </div>
                <div className="mt-3 flex items-end justify-between gap-4">
                  <div className="min-w-0 text-sm text-slate-500">
                    <div>{r.latest ? <>분석일 게시량 <b className="text-slate-800">{r.latest.post_count}건</b>{f?.baseline ? <span className="text-slate-400"> (평소 {Math.round(f.baseline)}건)</span> : null}</> : '분석 기록 없음'}</div>
                    <div className="mt-0.5">{r.issues_4w ? <>최근 4주 이슈 <b className="text-slate-800">{r.issues_4w}일</b></> : tx(t, 'floating_nav.no_issue', '최근 4주 이슈 없음')}</div>
                  </div>
                  <Spark days={r.days} height={36} barWidth={11} />
                </div>
                {r.level !== 'normal' && r.latest?.headline && (
                  <div className="mt-3 border-t border-slate-100 pt-3 text-sm text-slate-700">{r.latest.headline}</div>
                )}
                </div>
              </Card>
            </Link>
          )
        })}
      </div>
      {!!inactive.length && (
        <Section title="수집이 중단된 갤러리" hint="과거 기록만 볼 수 있습니다" className="mt-8">
          <div className="flex flex-wrap gap-2">
            {inactive.map(g => <Link key={g.gallery_id} href={`/gallery/${g.gallery_id}`} className="btn-ghost">{g.name} <Chip>중단</Chip></Link>)}
          </div>
        </Section>
      )}
    </div>
  )
}
