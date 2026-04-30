import type { DailyIssue, WeeklyData } from '@/types'

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function get<T>(path: string, revalidate = 300): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    next: { revalidate },
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) throw new Error(`${res.status} ${path}`)
  return res.json() as Promise<T>
}

export const api = {
  calendar:      () => get<{ issue_dates: string[]; weekly_dates: string[] }>('/api/calendar'),
  dailyLatest:   () => get<{ date?: string; issue_gallery_count?: number }>('/api/daily/latest', 120),
  dailyDates:    () => get<string[]>('/api/daily/dates'),
  dailyByDate:   (date: string) => get<DailyIssue[]>(`/api/daily/${date}`, 120),
  weeklyLatest:  () => get<{ week_start?: string; week_end?: string }>('/api/weekly/latest'),
  weeklyList:    () => get<string[]>('/api/weekly/list'),
  weeklyByWeek:  (ws: string) => get<WeeklyData>(`/api/weekly/${ws}`),
}
