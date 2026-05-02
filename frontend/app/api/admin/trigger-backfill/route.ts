import { NextRequest, NextResponse } from 'next/server'
import { getAdminPassword } from '@/lib/sheets'

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => ({}))
  const { password, __auth_check_only } = body

  const correct = await getAdminPassword()
  if (!correct || password !== correct) {
    return NextResponse.json({ error: 'unauthorized' }, { status: 401 })
  }

  // 비밀번호 확인만 요청한 경우 여기서 종료
  if (__auth_check_only) {
    return NextResponse.json({ ok: true })
  }

  const token = process.env.GITHUB_TOKEN
  const repo  = process.env.GITHUB_REPO ?? 'Kimmugil/DC-Pickaxe-Analytics'

  if (!token) {
    return NextResponse.json({ error: 'GITHUB_TOKEN not configured' }, { status: 500 })
  }

  const res = await fetch(
    `https://api.github.com/repos/${repo}/actions/workflows/backfill_tags.yml/dispatches`,
    {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ref: 'main', inputs: { limit: '0', dry_run: 'false' } }),
    },
  )

  if (!res.ok) {
    const text = await res.text()
    return NextResponse.json({ error: text }, { status: res.status })
  }

  return NextResponse.json({ ok: true })
}
