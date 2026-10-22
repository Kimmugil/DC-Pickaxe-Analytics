import { db } from './db'
import { LEVEL_RANK, levelOf, type Level } from './level'

/* 날짜(date) 컬럼은 항상 'YYYY-MM-DD' 문자열로 받는다(시간대 문제 방지). */

export type TopPost = { 제목: string; 링크: string; 날짜: string; 댓글수: number; 추천수: number; 조회수: number; 개념글?: boolean }
export type Issue = {
  title: string; detail: string; mention_count?: number; comment_sum?: number; share_posts?: number; share_comments?: number; keywords?: string[]; basis?: 'post' | 'speculation' | null; confidence?: string
  ref_posts?: { title: string; url: string; comment_count: number }[]
}
export type Flood = { title: string; count: number; authors?: number; kind?: string; reason?: string }
export type Report = {
  id: number; period_type: 'day' | 'week' | 'month'; start: string; end: string
  gallery_id: string | null; gallery_name: string | null
  post_count: number | null; avg_7d: number | null; avg_same_weekday: number | null
  issue_score: number | null; has_issue: boolean; is_borderline: boolean
  headline: string | null; summary: string | null; temperature_tag: string | null; top_cause: string | null
  category_scores: Record<string, { score: number; summary: string }> | null
  major_issues: Issue[] | null
  sentiment: Partial<Record<'positive' | 'negative', string | { summary: string; posts?: { title: string; url: string; comment_count: number }[]; quotes?: { text: string; title: string; url: string }[] }>> | null
  top_posts: TopPost[] | null
  keywords: [string, number][] | null
  daily_counts: Record<string, number> | null
  extra: Record<string, any> | null
}

/* 이관된 옛 방식 리포트(extra 없음)는 점수가 숫자가 낮게 고정된 데이터 기준이라 이슈가 과하게 많다.
   → 옛 방식 점수는 8점 이상만 '이슈', 그보다 낮은 옛 '이슈'는 '경계'로 보여준다. (DB 원본은 그대로) */
const ISSUE = `(r.has_issue and (r.extra->'score_parts' is not null or r.issue_score >= 8))`
const BORDER = `(r.is_borderline or (r.has_issue and r.extra->'score_parts' is null and r.issue_score < 8))`

const COLS = `r.id, r.period_type, to_char(r.period_start,'YYYY-MM-DD') as start, to_char(r.period_end,'YYYY-MM-DD') as "end",
  r.gallery_id, g.name as gallery_name, r.post_count, r.avg_7d::float as avg_7d, r.avg_same_weekday::float as avg_same_weekday,
  r.issue_score, ${ISSUE} as has_issue, ${BORDER} as is_borderline, r.headline, r.summary, r.temperature_tag, r.top_cause,
  r.category_scores, r.major_issues, r.sentiment, r.top_posts, r.keywords, r.daily_counts, r.extra`

export async function reportsOnDay(day: string): Promise<Report[]> {
  return (await db()`select ${db().unsafe(COLS)} from reports r left join galleries g using (gallery_id)
    where r.period_type = 'day' and r.period_start = ${day} order by r.issue_score desc nulls last, r.gallery_id`) as any
}

export async function latestDay(): Promise<string | null> {
  const [r] = await db()`select to_char(max(period_start),'YYYY-MM-DD') as d from reports where period_type = 'day'`
  return r?.d ?? null
}

export async function monthDays(month: string) {
  return (await db()`
    select to_char(r.period_start,'YYYY-MM-DD') as day, r.gallery_id, r.issue_score, ${db().unsafe(ISSUE)} as has_issue,
           ${db().unsafe(BORDER)} as is_borderline, r.headline, r.summary, (r.extra is not null) as modern
    from reports r where r.period_type = 'day' and to_char(r.period_start,'YYYY-MM') = ${month}
      and (r.has_issue or r.is_borderline) order by r.period_start`) as any as
    { day: string; gallery_id: string; issue_score: number; has_issue: boolean; is_borderline: boolean; headline: string | null; summary: string | null; modern: boolean }[]
}

export async function recentIssues(limit = 8): Promise<Report[]> {
  return (await db()`select ${db().unsafe(COLS)} from reports r left join galleries g using (gallery_id)
    where r.period_type = 'day' and ${db().unsafe(ISSUE)} order by r.period_start desc, r.issue_score desc limit ${limit}`) as any
}

export async function galleries() {
  return (await db()`
    select g.gallery_id, g.name, g.short_name, g.gallery_type, g.is_active, g.collect_interval_min, g.notes, (g.thumb is not null) as has_thumb,
           g.issue_threshold_adjust, g.min_issue_posts,
           to_char(g.last_collected_at at time zone 'Asia/Seoul','MM-DD HH24:MI') as last_collected, g.last_result,
           (select count(*)::int from reports r where r.gallery_id = g.gallery_id and r.period_type='day' and r.has_issue
              and r.period_start >= current_date - 28) as issues_4w,
           (select max(issue_score) from reports r where r.gallery_id = g.gallery_id and r.period_type='day'
              and r.period_start = (select max(period_start) from reports where period_type='day')) as last_score
    from galleries g order by g.is_active desc, issues_4w desc, g.name`) as any as {
      gallery_id: string; name: string; short_name: string | null; has_thumb: boolean; gallery_type: string; is_active: boolean; collect_interval_min: number; notes: string | null
      issue_threshold_adjust: number; min_issue_posts: number; last_collected: string | null; last_result: string | null
      issues_4w: number; last_score: number | null }[]
}

export async function galleryInfo(id: string) {
  const [g] = await db()`select gallery_id, name, short_name, (thumb is not null) as has_thumb, gallery_type, is_active, notes from galleries where gallery_id = ${id}`
  return g as { gallery_id: string; name: string; short_name: string | null; has_thumb: boolean; gallery_type: string; is_active: boolean; notes: string | null } | undefined
}

export async function galleryDays(id: string, days = 90) {
  return (await db()`
    select to_char(r.period_start,'YYYY-MM-DD') as day, r.post_count, r.issue_score, ${db().unsafe(ISSUE)} as has_issue,
           ${db().unsafe(BORDER)} as is_borderline, r.headline, (r.extra is not null) as modern
    from reports r where r.period_type = 'day' and r.gallery_id = ${id} and r.period_start >= current_date - ${days}::int
    order by r.period_start`) as any as
    { day: string; post_count: number; issue_score: number; has_issue: boolean; is_borderline: boolean; headline: string | null; modern: boolean }[]
}

export async function periodReports(type: 'week' | 'month', gid?: string): Promise<Report[]> {
  const sql = db()
  return (gid
    ? await sql`select ${sql.unsafe(COLS)} from reports r left join galleries g using (gallery_id)
        where r.period_type = ${type} and r.gallery_id = ${gid} order by r.period_start desc limit 30`
    : await sql`select ${sql.unsafe(COLS)} from reports r left join galleries g using (gallery_id)
        where r.period_type = ${type} and r.gallery_id is null order by r.period_start desc limit 60`) as any
}

export async function periodDetail(type: 'week' | 'month', start: string): Promise<{ overall: Report | null; rows: Report[] }> {
  const sql = db()
  const rows = (await sql`select ${sql.unsafe(COLS)} from reports r left join galleries g using (gallery_id)
    where r.period_type = ${type} and r.period_start = ${start} order by r.post_count desc nulls last`) as any as Report[]
  return { overall: rows.find(r => r.gallery_id === null) ?? null, rows: rows.filter(r => r.gallery_id !== null) }
}

export async function feedbackFor(reportId: number) {
  const rows = await db()`select target, verdict from report_feedback where report_id = ${reportId}`
  return Object.fromEntries(rows.map(r => [r.target as string, r.verdict as string])) as Record<string, string>
}



/* ── 홈 '상태판' ─────────────────────────────────────────── */
export type BoardDay = { day: string; count: number; level: Level }
export type BoardRow = { gallery_id: string; name: string; short_name: string | null; has_thumb: boolean; days: BoardDay[]; latest: Report | null; level: Level; issues_4w: number }

/** 최근 nDays 분석일 × 활성 갤러리의 상태. 홈 화면의 요약·상태표·주목 카드에 쓴다. */
export async function statusBoard(nDays = 7): Promise<{ dates: string[]; rows: BoardRow[]; reports: Report[] }> {
  const sql = db()
  const dates = (await sql`select to_char(d,'YYYY-MM-DD') as d from (select distinct period_start as d from reports
      where period_type = 'day' order by d desc limit ${nDays}) t order by d`).map(r => r.d as string)
  if (!dates.length) return { dates, rows: [], reports: [] }
  const reports = (await sql`select ${sql.unsafe(COLS)} from reports r left join galleries g using (gallery_id)
    where r.period_type = 'day' and r.period_start >= ${dates[0]} and g.is_active order by r.period_start`) as any as Report[]
  const gals = (await galleries()).filter(g => g.is_active)
  const rows: BoardRow[] = gals.map(g => {
    const mine = reports.filter(r => r.gallery_id === g.gallery_id)
    const days = dates.map(d => {
      const r = mine.find(x => x.start === d)
      return { day: d, count: r?.post_count ?? 0, level: r ? levelOf(r) : ('normal' as Level) }
    })
    const latest = mine.find(x => x.start === dates[dates.length - 1]) ?? null
    return { gallery_id: g.gallery_id, name: g.name, short_name: g.short_name, has_thumb: g.has_thumb, days, latest, level: latest ? levelOf(latest) : 'normal', issues_4w: g.issues_4w }
  })
  rows.sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level] || b.issues_4w - a.issues_4w || a.name.localeCompare(b.name))
  return { dates, rows, reports }
}

export async function recentWeeks(n = 1): Promise<Report[]> {
  const sql = db()
  return (await sql`select ${sql.unsafe(COLS)} from reports r left join galleries g using (gallery_id)
    where r.period_type = 'week' and r.gallery_id is null order by r.period_start desc limit ${n}`) as any
}


/** 한 갤러리의 한 달치 일간 리포트 (이슈·주목인 날만 카드로 보여주기 위해 전부 가져와 호출한 쪽에서 거른다) */
export async function galleryMonthReports(gid: string, month: string): Promise<Report[]> {
  const sql = db()
  return (await sql`select ${sql.unsafe(COLS)} from reports r left join galleries g using (gallery_id)
    where r.period_type = 'day' and r.gallery_id = ${gid} and to_char(r.period_start, 'YYYY-MM') = ${month}
    order by r.period_start desc`) as any
}
