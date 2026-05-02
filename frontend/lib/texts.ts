import { getUITextsRaw } from './sheets'

export async function getTexts(): Promise<Record<string, string>> {
  try {
    const rows = await getUITextsRaw()
    const map: Record<string, string> = {}
    for (const row of rows) {
      if (row.key) map[row.key] = row.value ?? ''
    }
    return map
  } catch {
    return {}
  }
}

/**
 * 키로 텍스트 조회. vars가 있으면 {placeholder} 치환.
 * 키 없을 시 fallback 반환.
 */
export function tp(
  t: Record<string, string>,
  key: string,
  vars?: Record<string, string | number>,
  fallback = '',
): string {
  const template = t[key] ?? fallback
  if (!vars) return template
  return template.replace(/\{(\w+)\}/g, (_, k) => String(vars[k] ?? ''))
}
