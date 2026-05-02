/**
 * Google Sheets 직접 읽기 (서버 전용)
 * googleapis를 사용해 Analytics 스프레드시트 3개 시트를 읽고 5분 캐싱.
 */

import { google } from 'googleapis'
import { unstable_cache } from 'next/cache'

function createClient() {
  const raw = process.env.GOOGLE_SERVICE_ACCOUNT_JSON
  if (!raw) throw new Error('GOOGLE_SERVICE_ACCOUNT_JSON env var is not set')
  const credentials = JSON.parse(raw)
  const auth = new google.auth.GoogleAuth({
    credentials,
    scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
  })
  return google.sheets({ version: 'v4', auth })
}

async function fetchSheet(sheetName: string): Promise<Record<string, string>[]> {
  const id = process.env.ANALYTICS_SPREADSHEET_ID
  if (!id) throw new Error('ANALYTICS_SPREADSHEET_ID env var is not set')

  const sheets = createClient()
  const res = await sheets.spreadsheets.values.get({
    spreadsheetId: id,
    range: sheetName,
  })

  const rows = (res.data.values ?? []) as string[][]
  if (rows.length < 2) return []

  const headers = rows[0]
  return rows
    .slice(1)
    .filter(row => row.some(cell => cell !== ''))
    .map(row => {
      const rec: Record<string, string> = {}
      headers.forEach((h, i) => { rec[h] = row[i] ?? '' })
      return rec
    })
}

export const getDailyIssuesRaw = unstable_cache(
  () => fetchSheet('daily_issues'),
  ['sheet:daily_issues'],
  { revalidate: 300 },
)

export const getWeeklyGalleriesRaw = unstable_cache(
  () => fetchSheet('weekly_galleries'),
  ['sheet:weekly_galleries'],
  { revalidate: 300 },
)

export const getWeeklyOverallRaw = unstable_cache(
  () => fetchSheet('weekly_overall'),
  ['sheet:weekly_overall'],
  { revalidate: 300 },
)

export const getUITextsRaw = unstable_cache(
  () => fetchSheet('ui_texts'),
  ['sheet:ui_texts'],
  { revalidate: 300 },
)
