import { revalidateTag } from 'next/cache'
import { NextResponse } from 'next/server'

export async function POST() {
  revalidateTag('sheet:daily_issues')
  revalidateTag('sheet:weekly_galleries')
  revalidateTag('sheet:weekly_overall')
  revalidateTag('sheet:ui_texts')
  return NextResponse.json({ ok: true })
}
