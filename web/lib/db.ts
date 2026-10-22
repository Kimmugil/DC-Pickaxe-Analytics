import dns from 'node:dns'
import postgres from 'postgres'

dns.setDefaultResultOrder('ipv4first')   // Vercel 빌드·실행 환경은 IPv6 바깥 접속이 안 되는 경우가 있어 IPv4를 먼저 쓴다

type Sql = ReturnType<typeof postgres>
const g = globalThis as unknown as { __sql?: Sql }

/** DB 연결은 처음 쓸 때 만든다(빌드 때 환경변수가 없어도 깨지지 않게). 개발 중 재시작해도 연결이 늘어나지 않게 전역에 보관. */
export function db(): Sql {
  if (!g.__sql) {
    const url = process.env.DATABASE_URL
    if (!url) throw new Error('DATABASE_URL 이 설정되지 않았습니다 (web/.env.local)')
    g.__sql = postgres(url, {
      prepare: false,                 // Supabase 풀러(트랜잭션 모드)와 호환
      max: 5,
      idle_timeout: 20,
      ssl: process.env.DB_SSL_INSECURE === '1' ? { rejectUnauthorized: false } : 'require',
    })
  }
  return g.__sql
}
