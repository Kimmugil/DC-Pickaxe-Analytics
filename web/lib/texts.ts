import { db } from './db'
import { DEF_BY_KEY } from './textDefs'

/** 관리자가 바꾼 문구(settings 표의 'ui.*'). 바꾸지 않은 문구는 없고, 기본값은 lib/textDefs.ts 에 있다. */
export async function getTexts(): Promise<Record<string, string>> {
  const rows = await db()`select key, value from settings where key like 'ui.%'`
  const out: Record<string, string> = {}
  for (const r of rows) out[(r.key as string).slice(3)] = (r.value as string) ?? ''
  return out
}

/** 문구 가져오기: 관리자가 바꾼 값 → 없으면 textDefs 의 기본값. {count} 같은 자리는 vars로 채운다. */
export function T(t: Record<string, string>, key: string, vars?: Record<string, string | number>): string {
  let s = t[key] || DEF_BY_KEY[key] || key
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v))
  return s
}

/** 예전 호출 방식 호환 (기본값을 직접 넘김) */
export function tx(t: Record<string, string>, key: string, fallback: string, vars?: Record<string, string | number>): string {
  let s = t[key] || fallback
  if (vars) for (const [k, v] of Object.entries(vars)) s = s.replaceAll(`{${k}}`, String(v))
  return s
}
