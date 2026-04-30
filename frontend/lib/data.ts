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

function toDaily(r: Record<string, string>): DailyIssue {
  return {
    date:             r.date ?? '',
    run_id:           r.run_id,
    gallery_id:       r.gallery_id ?? '',
    gallery_name:     r.gallery_name ?? '',
    posts_total:      Math.round(parseNum(r.posts_total)),
    avg_7d:           parseNum(r.avg_7d),
    avg_same_weekday: parseNum(r.avg_same_weekday),
    momentum_avg:     parseNum(r.momentum_avg),
    issue_score:      Math.round(parseNum(r.issue_score)),
    has_issue:        parseBool(r.has_issue),
    is_borderline:    parseBool(r.is_borderline),
    keywords:         parseField(r.keywords) as DailyIssue['keywords'],
    top_posts:        parseField(r.top_posts) as DailyIssue['top_posts'],
    ai_summary:       r.ai_summary ?? '',
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
  return rows.filter(r => r.date === date).map(toDaily)
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
