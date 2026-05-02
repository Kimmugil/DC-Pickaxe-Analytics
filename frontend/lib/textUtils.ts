/** 순수 텍스트 유틸 — 서버 의존성 없음, 클라이언트 컴포넌트에서 import 가능 */
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
