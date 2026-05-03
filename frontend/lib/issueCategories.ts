/** 이슈 카테고리 공유 상수 — 영어 키/한국어 키 모두 한국어 레이블로 정규화 */

export const CATEGORY_LABEL: Record<string, string> = {
  balance:   '밸런스',
  operation: '운영',
  bug:       '버그',
  payment:   '결제',
  content:   '컨텐츠',
  // 한국어 키 (구버전 호환)
  밸런스: '밸런스',
  운영:   '운영',
  버그:   '버그',
  결제:   '결제',
  컨텐츠: '컨텐츠',
  화제:   '화제',
  기타:   '기타',
}

export const CATEGORY_ORDER = ['balance', 'operation', 'bug', 'payment', 'content'] as const

/** issue_cause(영어 or 한국어)를 한국어 레이블로 정규화 */
export function normalizeCause(cause: string | null | undefined): string {
  if (!cause) return ''
  return CATEGORY_LABEL[cause] ?? cause
}

/** 화면 표시용 색상 (hex, Tailwind purge 우회) */
export const CAUSE_STYLE: Record<string, { bg: string; text: string }> = {
  밸런스: { bg: '#fef9c3', text: '#854d0e' },
  운영:   { bg: '#fff7ed', text: '#c2410c' },
  버그:   { bg: '#fee2e2', text: '#991b1b' },
  결제:   { bg: '#fdf4ff', text: '#7e22ce' },
  컨텐츠: { bg: '#eff6ff', text: '#1d4ed8' },
  화제:   { bg: '#f0fdf4', text: '#166534' },
  기타:   { bg: '#f9fafb', text: '#6b7280' },
}

/** 카테고리 필터 옵션 */
export const FILTER_OPTIONS = [
  { key: 'all',       label: '전체' },
  { key: 'balance',   label: '밸런스' },
  { key: 'operation', label: '운영' },
  { key: 'bug',       label: '버그' },
  { key: 'payment',   label: '결제' },
  { key: 'content',   label: '컨텐츠' },
] as const
