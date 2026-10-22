import { NextRequest, NextResponse } from 'next/server'
import { COOKIE_NAME, verifyToken } from '@/lib/session'

/** /admin 아래는 로그인 쿠키가 유효해야 접근 가능 (로그인 페이지 제외). 각 서버 액션에서도 다시 확인한다. */
export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  if (pathname === '/admin/login') return NextResponse.next()
  const ok = await verifyToken(req.cookies.get(COOKIE_NAME)?.value, process.env.SESSION_SECRET)
  if (ok) return NextResponse.next()
  const url = req.nextUrl.clone()
  url.pathname = '/admin/login'
  url.search = ''
  return NextResponse.redirect(url)
}

export const config = { matcher: ['/admin/:path*'] }
