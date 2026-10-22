import Link from 'next/link'
import { db } from '@/lib/db'
import { Card, Chip, PageHeader, Section, Tile } from '@/components/kit'

export const dynamic = 'force-dynamic'
export const maxDuration = 30

function ago(mins: number | null) {
  if (mins == null) return '기록 없음'
  if (mins < 60) return `${mins}분 전`
  if (mins < 1440) return `${Math.floor(mins / 60)}시간 전`
  return `${Math.floor(mins / 1440)}일 전`
}

export default async function AdminHome() {
  const sql = db()
  const [jobs, lastOk, gals, cov, cursors, size, blocked, ai, cfg] = await Promise.all([
    sql`select job, status, processed, left(coalesce(message,''), 200) as message,
               to_char(started_at at time zone 'Asia/Seoul','MM-DD HH24:MI') as at,
               round(extract(epoch from (coalesce(finished_at, now()) - started_at)))::int as sec
        from job_runs order by id desc limit 10`,
    sql`select job, round(extract(epoch from now() - max(finished_at)) / 60)::int as mins from job_runs
        where status in ('success', 'partial') and job in ('run', 'scrape', 'daily') group by job`,
    sql`select gallery_id, name, collect_interval_min as every,
               round(extract(epoch from now() - last_collected_at) / 60)::int as mins from galleries where is_active`,
    sql`select g.name, round(avg(c.completeness))::int as avg_c, min(c.completeness)::int as min_c
        from galleries g join daily_coverage c using (gallery_id)
        where g.is_active and c.day >= current_date - 14 group by 1 order by avg_c`,
    sql`select gallery_id, kind, last_page from crawl_cursor where not done`,
    sql`select pg_database_size(current_database())::bigint as bytes, (select greatest(reltuples, 0)::bigint from pg_class where oid = 'public.posts'::regclass) as posts`,
    sql`select value from settings where key = 'collector.blocked_until'`,
    sql`select coalesce(sum(calls), 0)::int as calls, coalesce(sum(input_tokens), 0)::bigint as tin, coalesce(sum(output_tokens), 0)::bigint as tout
        from ai_usage where day >= date_trunc('month', (now() at time zone 'Asia/Seoul')::date)`,
    sql`select key, value from settings where key in ('db.limit_mb', 'ai.price_in', 'ai.price_out')`,
  ])
  const okMins = Object.fromEntries(lastOk.map(r => [r.job as string, r.mins as number]))
  const collectMins = Math.min(okMins.run ?? 1e9, okMins.scrape ?? 1e9)
  const hasCollect = collectMins < 1e9
  const analyzeMins = okMins.daily as number | undefined
  const mb = Math.round(Number(size[0].bytes) / 1048576)
  const blockedUntil = blocked[0]?.value && new Date(blocked[0].value) > new Date() ? new Date(blocked[0].value) : null
  const conf = Object.fromEntries(cfg.map(r => [r.key as string, Number(r.value)])) as Record<string, number>
  const limitMb = conf['db.limit_mb'] || 8192                  // Supabase Pro 기본 8GB. 설정 화면에서 바꿀 수 있다
  const priceIn = conf['ai.price_in'] ?? 0.3, priceOut = conf['ai.price_out'] ?? 2.5      // 유료 요금(100만 토큰당 달러) — 추정용
  const aiCost = (Number(ai[0].tin) / 1e6) * priceIn + (Number(ai[0].tout) / 1e6) * priceOut
  const usedPct = (mb / limitMb) * 100

  const alerts: { tone: 'danger' | 'warn'; text: string; href?: string }[] = []
  if (blockedUntil) alerts.push({ tone: 'danger', text: `차단이 의심되어 수집을 쉬는 중입니다 (${blockedUntil.toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}까지)` })
  if (!hasCollect || collectMins > 180) alerts.push({ tone: collectMins > 720 || !hasCollect ? 'danger' : 'warn', text: `수집이 ${hasCollect ? ago(collectMins) : '아직'} 마지막으로 성공했습니다. 자동 실행이 연결되어 있는지 확인하세요.` })
  const failed = jobs.filter(j => j.status === 'failed')
  if (failed.length) alerts.push({ tone: 'danger', text: `최근 실행 중 실패 ${failed.length}건: ${failed[0].job} (${failed[0].at}) ${failed[0].message}` })
  const stale = gals.filter(g => g.mins != null && g.mins > g.every * 3 && g.mins > 180)
  const allStale = stale.length >= 3 || (stale.length > 0 && stale.length === gals.length)
  if (stale.length && !allStale) for (const g of stale) alerts.push({ tone: 'warn', text: `${g.name}: 마지막 수집이 ${ago(g.mins)}입니다 (주기 ${g.every}분)`, href: '/admin/galleries' })
  if (allStale && collectMins <= 180) alerts.push({ tone: 'warn', text: `${stale.length}개 갤러리의 마지막 수집이 오래됐습니다 (${stale.map(g => g.name).join(', ')})`, href: '/admin/galleries' })
  for (const c of cov) if (c.avg_c < 60) alerts.push({ tone: 'warn', text: `${c.name}: 최근 14일 수집 완성도 평균 ${c.avg_c}%`, href: undefined })
  for (const c of cursors) alerts.push({ tone: 'warn', text: `${c.gallery_id}: 누락 구간을 따라잡는 중입니다 (페이지 ${c.last_page}) — 끝나기 전에는 이 갤러리 분석이 보류됩니다` })
  if (usedPct > 90) alerts.push({ tone: 'danger', text: `DB 사용량이 ${mb}MB로 한도(${limitMb}MB)의 ${Math.round(usedPct)}%입니다.` })
  else if (usedPct > 70) alerts.push({ tone: 'warn', text: `DB 사용량이 ${mb}MB로 한도(${limitMb}MB)의 ${Math.round(usedPct)}%입니다.` })

  return (
    <div>
      <PageHeader title="현황" sub="수집과 분석이 잘 돌고 있는지, 확인할 문제가 있는지 보여줍니다" />

      <div className="mb-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label="마지막 수집 성공" value={hasCollect ? ago(collectMins) : '없음'} tone={!hasCollect || collectMins > 720 ? 'danger' : collectMins > 180 ? 'warn' : 'ok'} />
        <Tile label="마지막 분석 성공" value={ago(analyzeMins ?? null)} tone={analyzeMins == null || analyzeMins > 2880 ? 'warn' : 'ok'} />
        <Tile label="DB 사용량" value={`${mb >= 1024 ? (mb / 1024).toFixed(1) + 'GB' : mb + 'MB'}`} sub={`한도 ${limitMb >= 1024 ? (limitMb / 1024).toFixed(0) + 'GB' : limitMb + 'MB'}의 ${usedPct < 1 ? '1% 미만' : Math.round(usedPct) + '%'} · 글 ${Number(size[0].posts).toLocaleString()}건`} tone={usedPct > 90 ? 'danger' : usedPct > 70 ? 'warn' : 'default'} />
        <Tile label="이번 달 AI 사용량" value={`${ai[0].calls}회`} sub={`토큰 ${(Number(ai[0].tin) / 1000).toFixed(0)}K 입력 · ${(Number(ai[0].tout) / 1000).toFixed(0)}K 출력 · 유료 요금이라면 약 $${aiCost.toFixed(2)}`} />
      </div>

      <Section title="주의가 필요한 것">
        {alerts.length ? (
          <Card className="divide-y divide-slate-100">
            {alerts.map((a, i) => (
              <div key={i} className="flex items-start gap-3 px-4 py-3 text-sm">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${a.tone === 'danger' ? 'bg-rose-500' : 'bg-amber-400'}`} />
                <span className="flex-1 text-slate-700">{a.text}</span>
                {a.href && <Link href={a.href} className="shrink-0 text-xs text-indigo-700 hover:underline">보기</Link>}
              </div>
            ))}
          </Card>
        ) : <Card className="px-4 py-3 text-sm text-emerald-700">모든 항목이 정상입니다.</Card>}
      </Section>

      <Section title="최근 실행 기록" hint="최근 10건">
        <Card className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-slate-100 text-left text-xs text-slate-500"><th className="px-4 py-2 font-medium">시각</th><th className="font-medium">작업</th><th className="font-medium">결과</th><th className="font-medium">소요</th><th className="pr-4 font-medium">내용</th></tr></thead>
            <tbody>
              {jobs.map((j, i) => (
                <tr key={i} className="border-b border-slate-50 align-top last:border-0">
                  <td className="whitespace-nowrap px-4 py-2 text-slate-500">{j.at}</td>
                  <td className="py-2 font-medium">{j.job}</td>
                  <td className="py-2"><Chip tone={j.status === 'success' ? 'green' : j.status === 'failed' ? 'red' : j.status === 'partial' ? 'amber' : 'gray'}>{j.status === 'success' ? '성공' : j.status === 'failed' ? '실패' : j.status === 'partial' ? '일부 실패' : '진행 중'}</Chip></td>
                  <td className="whitespace-nowrap py-2 text-slate-500">{j.sec}초</td>
                  <td className="max-w-md truncate py-2 pr-4 text-xs text-slate-500" title={j.message}>{j.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      </Section>

      <Section title="수집 완성도" hint="최근 14일 · 글번호 범위 대비 저장 비율 (삭제된 글 때문에 100%가 아니어도 정상)">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {cov.map(c => (
            <Card key={c.name} className="flex items-center justify-between px-4 py-2.5 text-sm">
              <span className="font-medium">{c.name}</span>
              <span className={c.avg_c < 60 ? 'font-semibold text-rose-600' : 'text-slate-600'}>{c.avg_c}% <span className="text-xs text-slate-400">최저 {c.min_c}%</span></span>
            </Card>
          ))}
        </div>
      </Section>
    </div>
  )
}
