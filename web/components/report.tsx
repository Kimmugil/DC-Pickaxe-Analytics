import Link from 'next/link'
import type { Flood, Issue, Report, TopPost } from '@/lib/queries'
import { LEVEL_META, dayHref, levelOf, type Level } from '@/lib/level'
import { Card, Chip, Fold, Spark, StatusPill } from './kit'
import { setFeedback } from '@/app/admin/(panel)/actions'

/** 리포트 한 건에서 '숫자 근거'를 뽑는다 */
export function factsOf(r: Report) {
  const e = r.extra ?? {}
  const baseline = r.avg_same_weekday || r.avg_7d || 0
  const effective = e.effective_count ?? r.post_count ?? 0
  const ratio = baseline > 0 ? effective / baseline : null
  const topComments = r.top_posts?.length ? Math.max(...r.top_posts.map(p => p.댓글수)) : null
  return { baseline, effective, ratio, topComments, best: e.best_count as number | undefined, rising: (e.rising ?? []) as [string, number, number][] }
}

/** 숫자 근거를 한 줄의 담백한 글로: 뱃지를 늘어놓지 않는다 */
export function FactLine({ r }: { r: Report }) {
  const f = factsOf(r)
  const parts: React.ReactNode[] = []
  if (f.ratio != null) parts.push(f.ratio >= 1.15 || f.ratio <= 0.85 ? <span key="r">게시량 <b className="text-slate-800">평소의 {f.ratio.toFixed(1)}배</b></span> : <span key="r">게시량 평소 수준</span>)
  else if (r.post_count != null) parts.push(<span key="r">게시 {r.post_count}건</span>)
  if (f.topComments != null) parts.push(<span key="c">최다 댓글 <b className="text-slate-800">{f.topComments}개</b></span>)
  if (f.best) parts.push(<span key="b">개념글 {f.best}개</span>)
  if (f.rising.length) parts.push(<span key="u">급상승 <b className="text-slate-800">{f.rising.slice(0, 3).map(x => x[0]).join(' · ')}</b></span>)
  if (!parts.length) return null
  return <p className="flex flex-wrap gap-x-2 gap-y-0.5 text-sm text-slate-500">{parts.map((p, i) => <span key={i} className="inline-flex gap-2">{i > 0 && <span className="text-slate-300">·</span>}{p}</span>)}</p>
}

function Evidence({ it }: { it: Issue }) {
  if (!it.ref_posts?.length) return null
  return (
    <details className="group mt-1.5">
      <summary className="inline-flex cursor-pointer list-none items-center gap-1 text-xs text-indigo-700 hover:underline">
        <span className="transition-transform group-open:rotate-90">›</span>근거 글 {it.ref_posts.length}개
      </summary>
      <ul className="mt-1 space-y-0.5 border-l-2 border-slate-100 pl-3">
        {it.ref_posts.map((p, j) => (
          <li key={j} className="text-xs"><a href={p.url} target="_blank" rel="noreferrer" className="text-slate-700 hover:underline">{p.title}</a><span className="text-slate-400"> · 댓글 {p.comment_count}</span></li>
        ))}
      </ul>
    </details>
  )
}

/** 핵심 주제 목록. 번호 → 주제 이름(굵게) → 설명 → 관심 크기(관련 글·댓글) → 근거는 접힘 */
export function TopicList({ issues, feedback, ranked = false, scope = '그날', reportId, admin = false }: { issues: Issue[] | null; feedback?: Record<string, string>; ranked?: boolean; scope?: string; reportId?: number; admin?: boolean }) {
  if (!issues?.length) return null
  const rows = issues.map((it, i) => ({ it, i, v: feedback?.[`issue:${i}`] }))
  const shown = rows.filter(x => x.it.confidence !== '낮음' && !['wrong', 'weak'].includes(x.v ?? ''))
  const hidden = rows.filter(x => !shown.includes(x))
  const item = (x: (typeof rows)[number], n: number) => (
    <li key={n} className="flex gap-3">
      <span className={`mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-xs font-bold ${ranked && n === 1 ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600'}`}>{n}</span>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2">
          <span className="text-[15px] font-semibold text-slate-900">{x.it.title}</span>
          {x.it.basis === 'speculation'
            ? <span title="이 주제는 유저들의 짐작·예상·루머가 중심입니다. 확인된 사실이 아닙니다" className="rounded-md bg-amber-100 px-1.5 py-0.5 text-[11px] font-semibold text-amber-800">유저 추측 중심</span>
            : x.it.basis === 'post' ? <span title="글이나 댓글에 실제로 적힌 내용이 중심입니다" className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] font-medium text-slate-500">글 기준</span> : null}
          {!!x.it.mention_count && <span className="text-xs text-slate-400" title={x.it.keywords?.length ? `이 주제로 센 단어: ${x.it.keywords.join(', ')}` : undefined}>
            관련 글 {x.it.mention_count}건{x.it.share_posts != null ? ` (${scope}의 ${x.it.share_posts}%)` : ''}{x.it.comment_sum ? ` · 댓글 ${x.it.comment_sum.toLocaleString()}개` : ''}</span>}
          {x.v === 'wrong' && <Chip tone="red">관리자: 부정확</Chip>}
          {x.v === 'weak' && <Chip tone="amber">관리자: 근거 약함</Chip>}
        </div>
        <p className="mt-0.5 text-sm leading-relaxed text-slate-600">{x.it.detail}</p>
        <Evidence it={x.it} />
        {admin && reportId != null && (
          <form action={setFeedback} className="mt-1 inline-block">
            <input type="hidden" name="report_id" value={reportId} /><input type="hidden" name="target" value={`issue:${x.i}`} />
            <button name="verdict" value={x.v === 'wrong' ? 'clear' : 'wrong'} className="text-[11px] text-slate-300 hover:text-rose-600">{x.v === 'wrong' ? '부정확 신고 취소' : '이 주제가 부정확해요'}</button>
          </form>
        )}
      </div>
    </li>
  )
  return (
    <div>
      <ol className="space-y-4">{shown.map((x, i) => item(x, i + 1))}</ol>
      {!!hidden.length && (
        <details className="group mt-3">
          <summary className="cursor-pointer list-none text-xs text-slate-500 hover:text-slate-800"><span className="mr-1 inline-block transition-transform group-open:rotate-90">›</span>소규모 화제 {hidden.length}개 <span className="text-slate-400">(관련 글이 적거나 근거가 약해 접어 둠)</span></summary>
          <ol className="mt-3 space-y-4 opacity-80">{hidden.map((x, i) => item(x, shown.length + i + 1))}</ol>
        </details>
      )}
    </div>
  )
}

export function TopPostList({ posts }: { posts: TopPost[] | null }) {
  if (!posts?.length) return <p className="text-sm text-slate-400">기록 없음</p>
  return (
    <ul className="space-y-1.5">
      {posts.map((p, i) => (
        <li key={i} className="flex items-baseline gap-2 text-sm">
          <span className="w-4 shrink-0 text-xs text-slate-300">{i + 1}</span>
          <a href={p.링크} target="_blank" rel="noreferrer" className="flex-1 truncate text-slate-800 hover:underline">{p.제목}</a>
          {p.개념글 && <Chip tone="blue">개념글</Chip>}
          <span className="w-16 shrink-0 text-right text-xs text-slate-400">댓글 {p.댓글수}</span>
        </li>
      ))}
    </ul>
  )
}

export function FloodNote({ list }: { list?: Flood[] }) {
  if (!list?.length) return null
  return (
    <div className="rounded-lg bg-violet-50 px-3.5 py-2.5 text-sm text-violet-900">
      <div className="mb-1 text-xs font-semibold">같은 제목 반복 게시 (점수에는 묶음당 일부만 반영)</div>
      {list.map((f, i) => (
        <div key={i}>“{f.title}” {f.count}건{f.kind && f.kind !== '미분류' ? <> · <Chip tone="amber">{f.kind}</Chip></> : null}{f.reason ? <span className="text-xs text-violet-700"> {f.reason}</span> : null}</div>
      ))}
    </div>
  )
}

type Side = { summary: string; posts?: { title: string; url: string; comment_count: number }[]; quotes?: { text: string; title: string; url: string }[] }

/** 유저 반응: 근거(대표 댓글 인용 또는 근거 글)가 확인된 것만 보여준다. 근거 없는 요약은 저장 단계에서 버려진다. */
export function hasReactions(r: Report): boolean {
  const s = r.sentiment
  return !!s && ['positive', 'negative'].some(k => typeof s[k as 'positive' | 'negative'] === 'object')
}

function Reactions({ r }: { r: Report }) {
  const s = r.sentiment
  if (!s) return null
  const side = (k: 'positive' | 'negative', label: string, cls: string) => {
    const v = s[k]
    if (!v || typeof v === 'string') return null
    const d = v as Side
    return (
      <div className={`rounded-lg px-3.5 py-3 ${cls}`}>
        <p className="text-sm leading-relaxed"><b className="mr-1.5">{label}</b>{d.summary}</p>
        {!!d.quotes?.length && (
          <ul className="mt-2 space-y-1.5 border-t border-black/5 pt-2">
            {d.quotes.map((q, i) => (
              <li key={i} className="text-sm"><span className="text-slate-700">“{q.text}”</span>
                <a href={q.url} target="_blank" rel="noreferrer" className="ml-1.5 text-xs text-indigo-700 hover:underline">— {q.title}</a></li>
            ))}
          </ul>
        )}
        {!!d.posts?.length && (
          <p className="mt-2 text-xs text-slate-500">근거 글: {d.posts.map((p, i) => <span key={i}>{i > 0 && ' · '}<a href={p.url} target="_blank" rel="noreferrer" className="text-indigo-700 hover:underline">{p.title}</a></span>)}</p>
        )}
      </div>
    )
  }
  return <div className="grid gap-2.5 sm:grid-cols-2">{side('positive', '긍정', 'bg-emerald-50 text-emerald-950')}{side('negative', '부정', 'bg-rose-50 text-rose-950')}</div>
}

function Folds({ r }: { r: Report }) {
  const e = r.extra ?? {}
  return (
    <div className="border-t border-slate-100 bg-slate-50/60">
      {hasReactions(r) && <Fold title="유저 반응" hint="근거가 확인된 반응만 표시" open><Reactions r={r} /></Fold>}
      <Fold title="인기글" hint={`댓글 많은 순 ${r.top_posts?.length ?? 0}개`}><TopPostList posts={r.top_posts} /></Fold>
      {!!r.keywords?.length && <Fold title="주제 키워드"><div className="flex flex-wrap gap-1.5">{r.keywords.slice(0, 12).map(([w, c]) => <Chip key={w}>{w} {c}</Chip>)}</div></Fold>}
      {!!e.events_confirmed?.length && <Fold title="시간상 가까운 공식 이벤트" open><p className="text-sm text-slate-600">{e.events_confirmed.map((x: any) => `${x.date} ${x.title}`).join(' / ')}</p></Fold>}
    </div>
  )
}

function Caveats({ r }: { r: Report }) {
  const e = r.extra ?? {}
  const items = [
    r.period_type === 'day' && !r.extra && '예전 방식 점수',
    e.comment_baseline === false && '기준 기록 쌓이는 중',
    e.low_quality && '수집 일부 누락',
  ].filter(Boolean) as string[]
  return items.length ? <span className="text-xs text-amber-700">{items.join(' · ')}</span> : null
}

/**
 * 일간 리포트 카드. 읽는 순서 = 크기 순서:
 *   ① 헤드라인(가장 큼)  ② 요약  ③ 핵심 주제(번호)  ④ 숫자 한 줄  ⑤ 접힌 상세
 * 온도 이름·갤러리·날짜는 맨 위 작은 줄에만 둔다.
 */
export function DayCard({ r, feedback, level, compact = false, admin = false }: { r: Report; feedback?: Record<string, string>; level?: Level; compact?: boolean; admin?: boolean }) {
  const lv = level ?? levelOf(r)
  const e = r.extra ?? {}
  const big = lv === 'strong' || lv === 'issue'
  return (
    <Card level={lv}>
      <div className={`space-y-3 px-5 ${big ? 'py-5' : 'py-4'}`}>
        <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-sm">
          <StatusPill level={lv} />
          <Link href={`/gallery/${r.gallery_id}`} className="font-medium text-slate-700 hover:underline">{r.gallery_name}</Link>
          <span className="text-slate-400">{r.start}</span>
          <span className="ml-auto"><Caveats r={r} /></span>
        </div>
        {r.headline ? <h3 className={`${big ? 'text-2xl' : 'text-lg'} font-bold leading-snug tracking-tight text-slate-900`}>{r.headline}</h3>
          : <h3 className="text-base font-semibold text-slate-500">요약은 이슈로 분류된 날에만 만듭니다</h3>}
        {r.summary && <p className={`${big && !compact ? 'text-base' : 'text-sm'} leading-relaxed text-slate-700 ${compact ? 'line-clamp-3' : ''}`}>{r.summary}</p>}
        {big && !compact && !!r.major_issues?.length && (
          <div className="border-t border-slate-100 pt-3.5"><div className="mb-2.5 text-xs font-semibold text-slate-500">핵심 주제</div><TopicList issues={r.major_issues} feedback={feedback} reportId={r.id} admin={admin} /></div>
        )}
        {big && !compact && <FloodNote list={e.floods} />}
        <FactLine r={r} />
        {compact && <Link href={dayHref(r.gallery_id ?? '', r.start)} className="inline-block text-sm font-medium text-indigo-700 hover:underline">이날 상세 리포트 보기 →</Link>}
      </div>
      {big && !compact && <Folds r={r} />}
    </Card>
  )
}

/** 정상 갤러리 한 줄 */
export function NormalRow({ r }: { r: Report }) {
  const f = factsOf(r)
  return (
    <Link href={`/gallery/${r.gallery_id}`} className="flex items-center gap-3 px-4 py-2.5 text-sm hover:bg-slate-50">
      <span className="w-40 shrink-0 truncate font-medium text-slate-800">{r.gallery_name}</span>
      <span className="w-28 shrink-0 text-slate-500">{r.post_count ?? 0}건{f.baseline ? <span className="text-slate-300"> / 평소 {Math.round(f.baseline)}</span> : null}</span>
      <span className="flex-1 truncate text-xs text-slate-400">{r.keywords?.slice(0, 5).map(k => k[0]).join(' · ')}</span>
    </Link>
  )
}

/**
 * 주간·월간 리포트. 위에서 아래로: 기간 헤드라인 → 요약 → 관심 순위 → 평소와 달랐던 날 → 추이 → 접힌 상세.
 * 처음 읽는 사람이 '이 기간에 무엇이 가장 화제였는지'를 맨 위에서 알 수 있어야 한다.
 */
export function PeriodReport({ r, galleryId, kind }: { r: Report; galleryId: string; kind: '주간' | '월간' }) {
  const e = r.extra ?? {}
  const days = r.daily_counts ? Object.entries(r.daily_counts).sort(([a], [b]) => a.localeCompare(b)) : []
  const chips: { day: string; issue: boolean; watch: boolean; score: number; modern: boolean; headline: string | null }[] = e.days ?? []
  const lvOf = (c: (typeof chips)[number]): Level => levelOf({ has_issue: c.issue, is_borderline: c.watch, issue_score: c.score, extra: c.modern ? {} : null })
  const levelByDay = new Map(chips.map(c => [c.day, lvOf(c)]))
  const spark = days.map(([day, count]) => ({ day, count, level: (levelByDay.get(day) ?? 'normal') as Level }))
  return (
    <Card>
      <div className="space-y-4 px-5 py-5">
        <div className="text-xs font-medium text-slate-400">{kind} · 게시 {r.post_count ?? 0}건{e.issue_days ? ` · 평소와 달랐던 이슈 ${e.issue_days}일` : ''}</div>
        {r.headline ? <h3 className="text-2xl font-bold leading-snug tracking-tight text-slate-900">{r.headline}</h3> : <h3 className="text-base font-semibold text-slate-500">요약 없음</h3>}
        {r.summary && <p className="text-base leading-relaxed text-slate-700">{r.summary}</p>}
        {!!r.major_issues?.length && (
          <div className="border-t border-slate-100 pt-4"><div className="mb-3 text-xs font-semibold text-slate-500">이 기간 가장 화제가 된 것 (관심 순)</div><TopicList issues={r.major_issues} ranked scope={kind === '주간' ? '그 주' : '그 달'} /></div>
        )}
        {!!chips.length && (
          <div className="border-t border-slate-100 pt-4">
            <div className="mb-2 text-xs font-semibold text-slate-500">평소와 달랐던 날 · 누르면 그날 리포트로 이동</div>
            <div className="flex flex-wrap gap-2">
              {chips.map(c => {
                const lv = lvOf(c)
                return (
                  <Link key={c.day} href={dayHref(galleryId, c.day)} title={c.headline ?? ''} className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs hover:bg-slate-50">
                    <i className={`h-2 w-2 rounded-full ${LEVEL_META[lv].dot}`} /><span className="font-medium text-slate-700">{c.day.slice(5)}</span>
                    <span className="max-w-48 truncate text-slate-500">{c.headline ?? LEVEL_META[lv].label}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
        {spark.length > 1 && spark.length <= 40 && (
          <div className="border-t border-slate-100 pt-4"><div className="mb-2 text-xs font-semibold text-slate-500">일별 게시량</div><Spark days={spark} height={40} barWidth={spark.length > 14 ? 12 : 22} /></div>
        )}
      </div>
      <Folds r={r} />
    </Card>
  )
}
