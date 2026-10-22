import { createHash, scryptSync, timingSafeEqual } from 'node:crypto'
import { cookies, headers } from 'next/headers'
import { redirect } from 'next/navigation'
import { db } from './db'
import { COOKIE_NAME, verifyToken } from './session'

const WINDOW_MIN = 15
const MAX_FAILS_PER_IP = 5
const MAX_FAILS_TOTAL = 30

/** 저장 형식: scrypt:N:salt(hex):hash(hex)  — tools/set_admin_password.py 로 만든다 */
export function verifyPassword(password: string, stored: string | undefined): boolean {
  if (!stored) return false
  const [scheme, n, salt, hash] = stored.split(':')
  if (scheme !== 'scrypt' || !n || !salt || !hash) return false
  const expected = Buffer.from(hash, 'hex')
  const actual = scryptSync(password, Buffer.from(salt, 'hex'), expected.length, { N: Number(n), r: 8, p: 1 })
  return expected.length === actual.length && timingSafeEqual(expected, actual)
}

export async function clientKey(): Promise<string> {
  const h = await headers()
  const ip = (h.get('x-forwarded-for') ?? '').split(',')[0].trim() || 'local'
  return createHash('sha256').update(ip + (process.env.SESSION_SECRET ?? '')).digest('hex').slice(0, 24)
}

/** 최근 15분 실패 횟수로 잠금 여부 판단 (IP별 5회, 전체 30회) */
export async function isLocked(key: string): Promise<boolean> {
  const sql = db()
  const [r] = await sql`
    select count(*) filter (where ip_hash = ${key})::int as mine, count(*)::int as total
    from admin_login_attempts
    where not success and created_at > now() - make_interval(mins => ${WINDOW_MIN})`
  return r.mine >= MAX_FAILS_PER_IP || r.total >= MAX_FAILS_TOTAL
}

export async function recordAttempt(key: string, success: boolean) {
  await db()`insert into admin_login_attempts (ip_hash, success) values (${key}, ${success})`
}

export async function isAdmin(): Promise<boolean> {
  const c = await cookies()
  return verifyToken(c.get(COOKIE_NAME)?.value, process.env.SESSION_SECRET)
}

/** 서버 액션·관리자 페이지 맨 앞에서 호출. 미들웨어가 뚫려도 여기서 한 번 더 막는다. */
export async function requireAdmin() {
  if (!(await isAdmin())) redirect('/admin/login')
}
