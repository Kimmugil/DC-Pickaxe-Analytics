/** 서명된 세션 쿠키. Web Crypto 만 써서 미들웨어(Edge)와 서버 양쪽에서 동작한다. */
const enc = new TextEncoder()

function b64url(buf: ArrayBuffer | Uint8Array): string {
  const bytes = buf instanceof Uint8Array ? buf : new Uint8Array(buf)
  let s = ''
  bytes.forEach(b => (s += String.fromCharCode(b)))
  return btoa(s).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '')
}

async function sign(data: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey('raw', enc.encode(secret), { name: 'HMAC', hash: 'SHA-256' }, false, ['sign'])
  return b64url(await crypto.subtle.sign('HMAC', key, enc.encode(data)))
}

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let diff = 0
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return diff === 0
}

export const COOKIE_NAME = 'dcp_admin'
export const SESSION_TTL_SEC = 60 * 60 * 12

export async function makeToken(secret: string): Promise<string> {
  const payload = `${Math.floor(Date.now() / 1000) + SESSION_TTL_SEC}`
  return `${payload}.${await sign(payload, secret)}`
}

export async function verifyToken(token: string | undefined, secret: string | undefined): Promise<boolean> {
  if (!token || !secret) return false
  const [payload, sig] = token.split('.')
  if (!payload || !sig) return false
  if (!safeEqual(sig, await sign(payload, secret))) return false
  return Number(payload) > Math.floor(Date.now() / 1000)
}
