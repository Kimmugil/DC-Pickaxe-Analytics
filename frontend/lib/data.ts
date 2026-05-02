/**
 * 데이터 접근 함수 — 서버 컴포넌트에서 직접 import해서 사용.
 * Google Sheets raw 데이터를 파싱해 타입이 맞는 객체로 변환.
 */

import type { DailyIssue, WeeklyGallery, WeeklyData } from '@/types'
import { getDailyIssuesRaw, getWeeklyGalleriesRaw, getWeeklyOverallRaw } from './sheets'

// ── 파싱 헬퍼 ──────────────────────────────────────────────────────────

function parseField(v: string | undefined): unknown {
  if (!v) return null
  const s = v.trim()
  if (!s || s === 'nan' || s === 'None') return null
  // JSON 먼저 시도
  try { return JSON.parse(s) } catch {}
  // Python repr (single quotes) → JSON 변환
  try {
    return JSON.parse(
      s.replace(/'/g, '"')
       .replace(/\bTrue\b/g, 'true')
       .replace(/\bFalse\b/g, 'false')
       .replace(/\bNone\b/g, 'null'),
    )
  } catch {}
  return s
}

function parseBool(v: string | undefined): boolean {
  if (!v) return false
  const s = v.trim().toLowerCase()
  return s === '1' || s === 'true'
}

function parseNum(v: string | undefined, fallback = 0): number {
  const n = parseFloat(v ?? '')
  return isNaN(n) ? fallback : n
}

function toDaily(r: Record<string, string>, recentIssueDays?: number): DailyIssue {
  return {
    date:              r.date ?? '',
    run_id:            r.run_id,
    gallery_id:        r.gallery_id ?? '',
    gallery_name:      r.gallery_name ?? '',
    posts_total:       Math.round(parseNum(r.posts_total)),
    avg_7d:            parseNum(r.avg_7d),
    avg_same_weekday:  parseNum(r.avg_same_weekday),
    momentum_avg:      parseNum(r.momentum_avg),
    issue_score:       Math.round(parseNum(r.issue_score)),
    has_issue:         parseBool(r.has_issue),
    is_borderline:     parseBool(r.is_borderline),
    keywords:          parseField(r.keywords) as DailyIssue['keywords'],
    top_posts:         parseField(r.top_posts) as DailyIssue['top_posts'],
    ai_summary:        r.ai_summary ?? '',
    temperature_tag:   r.temperature_tag || undefined,
    issue_cause:       r.issue_cause || undefined,
    recent_issue_days: recentIssueDays,
  }
}

function toWeekly(r: Record<string, string>): WeeklyGallery {
  return {
    week_start:   r.week_start ?? '',
    week_end:     r.week_end ?? '',
    run_id:       r.run_id,
    gallery_id:   r.gallery_id ?? '',
    gallery_name: r.gallery_name ?? '',
    total_posts:  Math.round(parseNum(r.total_posts)),
    daily_counts: parseField(r.daily_counts) as WeeklyGallery['daily_counts'],
    keywords:     parseField(r.keywords) as WeeklyGallery['keywords'],
    top_posts:    parseField(r.top_posts) as WeeklyGallery['top_posts'],
    ai_summary:   r.ai_summary ?? '',
  }
}

// ── Public API ─────────────────────────────────────────────────────────

export async function getCalendarData() {
  const [daily, weekly] = await Promise.all([
    getDailyIssuesRaw(),
    getWeeklyGalleriesRaw(),
  ])
  const issueDates = [...new Set(
    daily.filter(r => parseBool(r.has_issue)).map(r => r.date).filter(Boolean),
  )].sort((a, b) => b.localeCompare(a))

  const weeklyDates = [...new Set(
    weekly.map(r => r.week_start).filter(Boolean),
  )].sort((a, b) => b.localeCompare(a))

  return { issue_dates: issueDates, weekly_dates: weeklyDates }
}

export async function getLatestDailyInfo() {
  const rows = await getDailyIssuesRaw()
  const issueRows = rows.filter(r => parseBool(r.has_issue))
  if (!issueRows.length) return null

  const latest = issueRows
    .map(r => r.date)
    .filter(Boolean)
    .sort((a, b) => b.localeCompare(a))[0]

  const count = issueRows.filter(r => r.date === latest).length
  return { date: latest, issue_gallery_count: count }
}

export async function getDailyIssueDates(): Promise<string[]> {
  const rows = await getDailyIssuesRaw()
  return [...new Set(
    rows.filter(r => parseBool(r.has_issue)).map(r => r.date).filter(Boolean),
  )].sort((a, b) => b.localeCompare(a))
}

export async function getDailyByDate(date: string): Promise<DailyIssue[]> {
  const rows = await getDailyIssuesRaw()

  // Count recent issue days per gallery in the 28 days before target date
  const cutoff = new Date(date + 'T00:00:00Z')
  cutoff.setUTCDate(cutoff.getUTCDate() - 28)
  const cutoffStr = cutoff.toISOString().slice(0, 10)

  const recentMap = new Map<string, Set<string>>()
  for (const r of rows) {
    if (!r.gallery_id || !r.date) continue
    if (r.date >= date || r.date < cutoffStr) continue
    if (!parseBool(r.has_issue)) continue
    if (!recentMap.has(r.gallery_id)) recentMap.set(r.gallery_id, new Set())
    recentMap.get(r.gallery_id)!.add(r.date)
  }

  return rows
    .filter(r => r.date === date)
    .map(r => toDaily(r, recentMap.get(r.gallery_id)?.size ?? 0))
}

export async function getWeeklyList(): Promise<string[]> {
  const rows = await getWeeklyGalleriesRaw()
  return [...new Set(rows.map(r => r.week_start).filter(Boolean))]
    .sort((a, b) => b.localeCompare(a))
}

export async function getLatestWeeklyInfo() {
  const rows = await getWeeklyOverallRaw()
  if (!rows.length) return null
  const sorted = [...rows].sort((a, b) =>
    (b.week_start ?? '').localeCompare(a.week_start ?? ''),
  )
  const r = sorted[0]
  return { week_start: r.week_start ?? '', week_end: r.week_end ?? '' }
}

export async function getDailyIssueList(): Promise<{
  date: string
  issue_count: number
  borderline_count: number
  max_score: number
  top_galleries: { name: string; score: number }[]
}[]> {
  const rows = await getDailyIssuesRaw()

  const byDate = new Map<string, Record<string, string>[]>()
  for (const r of rows) {
    if (!r.date) continue
    if (!byDate.has(r.date)) byDate.set(r.date, [])
    byDate.get(r.date)!.push(r)
  }

  const result: {
    date: string
    issue_count: number
    borderline_count: number
    max_score: number
    top_galleries: { name: string; score: number }[]
  }[] = []

  for (const [date, dateRows] of byDate) {
    const issueRows = dateRows.filter(r => parseBool(r.has_issue))
    if (issueRows.length === 0) continue
    const borderRows = dateRows.filter(r => !parseBool(r.has_issue) && parseBool(r.is_borderline))
    const sorted = [...issueRows].sort((a, b) => parseNum(b.issue_score) - parseNum(a.issue_score))
    result.push({
      date,
      issue_count: issueRows.length,
      borderline_count: borderRows.length,
      max_score: Math.round(parseNum(sorted[0]?.issue_score ?? '0')),
      top_galleries: sorted.slice(0, 3).map(r => ({
        name: r.gallery_name ?? '',
        score: Math.round(parseNum(r.issue_score)),
      })),
    })
  }

  return result.sort((a, b) => b.date.localeCompare(a.date))
}

export async function getWeeklyListWithInfo(): Promise<{
  week_start: string
  week_end: string
  gallery_count: number
  ai_summary: string
}[]> {
  const [galRows, overallRows] = await Promise.all([
    getWeeklyGalleriesRaw(),
    getWeeklyOverallRaw(),
  ])

  const weekGalleries = new Map<string, Set<string>>()
  for (const r of galRows) {
    if (!r.week_start || !r.gallery_id) continue
    if (!weekGalleries.has(r.week_start)) weekGalleries.set(r.week_start, new Set())
    weekGalleries.get(r.week_start)!.add(r.gallery_id)
  }

  const overallMap = new Map<string, Record<string, string>>()
  for (const r of overallRows) {
    if (!r.week_start) continue
    const existing = overallMap.get(r.week_start)
    if (!existing || (r.run_id ?? '') > (existing.run_id ?? '')) {
      overallMap.set(r.week_start, r)
    }
  }

  return Array.from(weekGalleries.entries())
    .map(([week_start, gallerySet]) => {
      const overall = overallMap.get(week_start)
      const fallbackEnd = new Date(week_start + 'T00:00:00')
      fallbackEnd.setDate(fallbackEnd.getDate() + 6)
      return {
        week_start,
        week_end: overall?.week_end ?? fallbackEnd.toISOString().slice(0, 10),
        gallery_count: gallerySet.size,
        ai_summary: overall?.ai_summary ?? '',
      }
    })
    .sort((a, b) => b.week_start.localeCompare(a.week_start))
}

export async function getGalleryList(): Promise<{
  id: string
  name: string
  recent_issue_days: number
  latest_issue: { score: number; date: string } | null
}[]> {
  const rows = await getDailyIssuesRaw()

  const nameMap = new Map<string, string>()
  const issueDates = new Map<string, Set<string>>()
  const latestIssue = new Map<string, { score: number; date: string }>()

  const cutoff = new Date()
  cutoff.setUTCDate(cutoff.getUTCDate() - 28)
  const cutoffStr = cutoff.toISOString().slice(0, 10)

  for (const r of rows) {
    if (!r.gallery_id) continue
    if (r.gallery_name) nameMap.set(r.gallery_id, r.gallery_name)
    if (!parseBool(r.has_issue)) continue
    if (r.date && r.date >= cutoffStr) {
      if (!issueDates.has(r.gallery_id)) issueDates.set(r.gallery_id, new Set())
      issueDates.get(r.gallery_id)!.add(r.date)
    }
    const existing = latestIssue.get(r.gallery_id)
    if (!existing || (r.date ?? '') > existing.date) {
      latestIssue.set(r.gallery_id, {
        score: Math.round(parseNum(r.issue_score)),
        date: r.date ?? '',
      })
    }
  }

  return Array.from(nameMap.entries())
    .map(([id, name]) => ({
      id,
      name,
      recent_issue_days: issueDates.get(id)?.size ?? 0,
      latest_issue: latestIssue.get(id) ?? null,
    }))
    .sort((a, b) => b.recent_issue_days - a.recent_issue_days || a.name.localeCompare(b.name))
}

export async function getGalleryHistory(galleryId: string): Promise<{
  gallery_name: string
  issues: DailyIssue[]
  weeklies: WeeklyGallery[]
}> {
  const [dailyRows, weeklyRows] = await Promise.all([
    getDailyIssuesRaw(),
    getWeeklyGalleriesRaw(),
  ])

  const myDaily = dailyRows.filter(r => r.gallery_id === galleryId)
  const gallery_name =
    myDaily.find(r => r.gallery_name)?.gallery_name ??
    weeklyRows.find(r => r.gallery_id === galleryId)?.gallery_name ??
    galleryId

  const issues = myDaily
    .filter(r => parseBool(r.has_issue) || parseBool(r.is_borderline))
    .map(r => toDaily(r))
    .sort((a, b) => b.date.localeCompare(a.date))

  // gallery_id 기준 최신 run만 유지 (week_start 별)
  const weekMap = new Map<string, Record<string, string>>()
  for (const r of weeklyRows.filter(r => r.gallery_id === galleryId)) {
    const existing = weekMap.get(r.week_start)
    if (!existing || (r.run_id ?? '') > (existing.run_id ?? '')) {
      weekMap.set(r.week_start, r)
    }
  }
  const weeklies = Array.from(weekMap.values())
    .map(toWeekly)
    .sort((a, b) => b.week_start.localeCompare(a.week_start))

  return { gallery_name, issues, weeklies }
}

export async function getWeeklyByWeek(weekStart: string): Promise<WeeklyData> {
  const [galRows, overallRows] = await Promise.all([
    getWeeklyGalleriesRaw(),
    getWeeklyOverallRaw(),
  ])

  // gallery_id 기준 최신 run만 유지
  const galleryMap = new Map<string, Record<string, string>>()
  galRows
    .filter(r => r.week_start === weekStart)
    .forEach(r => galleryMap.set(r.gallery_id, r))

  const galleries = Array.from(galleryMap.values()).map(toWeekly)

  const overallRow = [...overallRows]
    .filter(r => r.week_start === weekStart)
    .sort((a, b) => (b.run_id ?? '').localeCompare(a.run_id ?? ''))[0]

  return {
    galleries,
    overall: overallRow
      ? {
          week_start: overallRow.week_start,
          week_end:   overallRow.week_end,
          ai_summary: overallRow.ai_summary,
        }
      : {},
  }
}
