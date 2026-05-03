import { NextRequest, NextResponse } from 'next/server'
import { getAdminPassword } from '@/lib/sheets'

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  const { password, start_date, end_date, dry_run } = body

  const correct = await getAdminPassword()
  if (!correct || password !== correct) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  if (!start_date || !end_date) {
    return NextResponse.json({ error: 'start_date / end_date 필수' }, { status: 400 })
  }

  const token = process.env.GITHUB_TOKEN
  const repo  = process.env.GITHUB_REPO ?? 'Kimmugil/DC-Pickaxe-Analytics'

  if (!token) {
    return NextResponse.json({ error: 'GITHUB_TOKEN not configured' }, { status: 500 })
  }

  const inputs: Record<string, string> = {
    start_date,
    end_date,
    dry_run: dry_run ? 'true' : 'false',
  }

  const res = await fetch(
    `https://api.github.com/repos/${repo}/actions/workflows/backfill_weekly.yml/dispatches`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ref: 'main', inputs }),
    },
  )

  if (!res.ok) {
    const text = await res.text()
    return NextResponse.json({ error: text }, { status: res.status })
  }

  return NextResponse.json({ ok: true })
}
