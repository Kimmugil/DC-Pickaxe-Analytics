import { LEVEL_META, levelOf, type Level } from '@/lib/level'

type D = { day: string; post_count: number; has_issue: boolean; is_borderline: boolean; issue_score: number; modern: boolean }

/** 일별 게시량 막대 그래프 (서버에서 그리는 SVG). 색은 그날의 상태 단계. */
export function Bars({ days, height = 160 }: { days: D[]; height?: number }) {
  if (!days.length) return <p className="text-sm text-slate-400">기록 없음</p>
  const W = 900, pad = 4, H = height
  const max = Math.max(...days.map(d => d.post_count || 0), 1)
  const bw = (W - pad * 2) / days.length
  return (
    <svg viewBox={`0 0 ${W} ${H + 22}`} className="h-auto w-full" role="img" aria-label="일별 게시량">
      {[0.5, 1].map(f => <line key={f} x1={pad} x2={W - pad} y1={H - f * H + 0.5} y2={H - f * H + 0.5} stroke="#e2e8f0" strokeDasharray="3 4" />)}
      {days.map((d, i) => {
        const lv: Level = levelOf({ ...d, extra: d.modern ? {} : null })
        const h = Math.max(1.5, ((d.post_count || 0) / max) * H)
        return (
          <rect key={d.day} x={pad + i * bw + 0.5} y={H - h} width={Math.max(1.2, bw - 1.5)} height={h} fill={LEVEL_META[lv].bar} rx={1.5}>
            <title>{`${d.day} · ${d.post_count}건 · ${LEVEL_META[lv].label}`}</title>
          </rect>
        )
      })}
      <text x={pad} y={H + 16} fontSize="11" fill="#94a3b8">{days[0].day}</text>
      <text x={W - pad} y={H + 16} fontSize="11" fill="#94a3b8" textAnchor="end">{days[days.length - 1].day}</text>
      <text x={W - pad} y={11} fontSize="11" fill="#94a3b8" textAnchor="end">최대 {max}건</text>
    </svg>
  )
}
