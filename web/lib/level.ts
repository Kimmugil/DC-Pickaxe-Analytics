/** 화면 전체에서 쓰는 '온도'. 점수 숫자 대신 이 단계를 보여준다 (회색 → 노랑 → 주황 → 빨강). */
export type Level = 'strong' | 'issue' | 'watch' | 'normal'

export const LEVEL_META: Record<Level, { label: string; help: string; pill: string; chip: string; dot: string; bar: string; ring: string }> = {
  strong: { label: '강한 이슈', help: '평소보다 훨씬 크게 달랐던 날', pill: 'bg-red-600 text-white', chip: 'bg-red-600 text-white', dot: 'bg-red-600', bar: '#dc2626', ring: 'border-red-300' },
  issue:  { label: '이슈',     help: '평소와 확연히 달랐던 날',     pill: 'bg-orange-500 text-white', chip: 'bg-orange-500 text-white', dot: 'bg-orange-500', bar: '#f97316', ring: 'border-orange-300' },
  watch:  { label: '주목',     help: '평소보다 조금 활발했던 날 (이슈 직전)', pill: 'bg-yellow-100 text-yellow-800', chip: 'bg-yellow-200 text-yellow-900', dot: 'bg-yellow-400', bar: '#facc15', ring: 'border-yellow-300' },
  normal: { label: '평온',     help: '평소 수준',                  pill: 'bg-slate-100 text-slate-600', chip: 'bg-slate-100 text-slate-500', dot: 'bg-slate-300', bar: '#cbd5e1', ring: 'border-slate-200' },
}

type Lvl = { has_issue: boolean; is_borderline: boolean; issue_score: number | null; extra?: unknown | null }

/** 새 방식 점수는 6점 이상, 이관된 옛 방식 점수는 9점 이상이면 '강한 이슈' */
export function levelOf(r: Lvl): Level {
  const legacy = !r.extra
  if (r.has_issue) return (r.issue_score ?? 0) >= (legacy ? 9 : 6) ? 'strong' : 'issue'
  return r.is_borderline ? 'watch' : 'normal'
}

export const LEVEL_RANK: Record<Level, number> = { strong: 3, issue: 2, watch: 1, normal: 0 }

export const LEVELS_DESC: Level[] = ['strong', 'issue', 'watch', 'normal']

/** 갤러리 약칭: 관리자가 정한 short_name, 없으면 이름에서 '키우기'를 뗀 앞부분 */
export function shortName(g: { name: string; short_name?: string | null }): string {
  return g.short_name || g.name.replace(/\s*키우기$/, '').slice(0, 6)
}

/** 일별 리포트 카드로 바로 가는 주소 (갤러리 페이지의 해당 월 + 카드 위치) */
export function dayHref(galleryId: string, day: string): string {
  return `/gallery/${galleryId}?month=${day.slice(0, 7)}#d-${day}`
}
