import dns from 'node:dns'
import postgres from 'postgres'

dns.setDefaultResultOrder('ipv4first')   // Vercel 빌드·실행 환경은 IPv6 바깥 접속이 안 되는 경우가 있어 IPv4를 먼저 쓴다

type Sql = ReturnType<typeof postgres>
const g = globalThis as unknown as { __sql?: Sql }

/** DB 연결은 처음 쓸 때 만든다(빌드 때 환경변수가 없어도 깨지지 않게). 개발 중 재시작해도 연결이 늘어나지 않게 전역에 보관. */
export function db(): Sql {
  if (!g.__sql) {
    const raw = process.env.DATABASE_URL
    if (!raw) throw new Error('DATABASE_URL 이 설정되지 않았습니다 (web/.env.local)')
    // 반드시 '세션 풀러'(5432)로 접속한다. 트랜잭션 풀러(6543)는 질의가 연결 수보다 많이 몰리면 연결 묶음 전체가 멈추고 복구되지 않는 현상이
    // 실험으로 확인됐다(2026-10). 대신 서버 한 곳당 연결 1개만 쓰고 놀면 곧 닫아, 세션 풀러의 총 한도(15개, 다른 사이트와 같이 씀)를 아낀다.
    const url = raw.replace(/:6543\//, ':5432/')
    g.__sql = postgres(url, {
      prepare: false,                 // 풀러 환경에서는 이름 붙은 prepared statement 를 쓰지 않음
      max: 1,
      idle_timeout: 3,
      ssl: process.env.DB_SSL_INSECURE === '1' ? { rejectUnauthorized: false } : 'require',
    })
  }
  return g.__sql
}
