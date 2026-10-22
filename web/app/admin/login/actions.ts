'use server'
import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { clientKey, isLocked, recordAttempt, verifyPassword } from '@/lib/auth'
import { COOKIE_NAME, SESSION_TTL_SEC, makeToken } from '@/lib/session'

export async function login(_prev: { error: string }, form: FormData): Promise<{ error: string }> {
  const secret = process.env.SESSION_SECRET
  const hash = process.env.ADMIN_PASSWORD_HASH
  if (!secret || !hash) return { error: '관리자 비밀번호가 아직 설정되지 않았습니다. (tools/set_admin_password.py 실행)' }
  const key = await clientKey()
  if (await isLocked(key)) return { error: '로그인 시도가 너무 많습니다. 15분 뒤에 다시 시도하세요.' }
  const ok = verifyPassword(String(form.get('password') ?? ''), hash)
  await recordAttempt(key, ok)
  if (!ok) return { error: '비밀번호가 맞지 않습니다.' }
  const c = await cookies()
  c.set(COOKIE_NAME, await makeToken(secret), {
    httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'lax', path: '/', maxAge: SESSION_TTL_SEC,
  })
  redirect('/admin')
}

export async function logout() {
  const c = await cookies()
  c.delete(COOKIE_NAME)
  redirect('/')
}
