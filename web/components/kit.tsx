/** 디자인 키트: 모든 화면이 같은 부품을 쓴다 (색은 상태 표시에만, 나머지는 슬레이트 회색 + 포인트 하나). */
import Link from 'next/link'
import { LEVEL_META, type Level } from '@/lib/level'

export function StatusPill({ level, className = '' }: { level: Level; className?: string }) {
  const m = LEVEL_META[level]
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap ${m.pill} ${className}`}>{m.label}</span>
}

export function Dot({ level }: { level: Level }) {
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${LEVEL_META[level].dot}`} aria-hidden />
}

/** 온도 범례: 캘린더·상태표 근처에 항상 둔다. 마우스를 올리면 뜻이 보인다. */
export function Legend({ className = '' }: { className?: string }) {
  return (
    <div className={`flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 ${className}`}>
      <span className="font-medium text-slate-600">온도</span>
      {(['normal', 'watch', 'issue', 'strong'] as Level[]).map(l => (
        <span key={l} className="inline-flex items-center gap-1.5" title={LEVEL_META[l].help}>
          <span className={`inline-block h-2.5 w-2.5 rounded-full ${LEVEL_META[l].dot}`} />
          <span>{LEVEL_META[l].label}</span>
          <span className="hidden text-slate-400 lg:inline">· {LEVEL_META[l].help}</span>
        </span>
      ))}
    </div>
  )
}

export function PageHeader({ title, sub, right }: { title: string; sub?: React.ReactNode; right?: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-end gap-x-4 gap-y-2 mb-6">
      <div className="min-w-0">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">{title}</h1>
        {sub && <p className="text-sm text-slate-500 mt-1">{sub}</p>}
      </div>
      {right && <div className="ml-auto flex items-center gap-2">{right}</div>}
    </div>
  )
}

export function Section({ title, hint, right, children, className = '' }: {
  title: string; hint?: React.ReactNode; right?: React.ReactNode; children: React.ReactNode; className?: string
}) {
  return (
    <section className={`mb-8 ${className}`}>
      <div className="flex items-baseline gap-3 mb-3">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {hint && <span className="text-xs text-slate-500">{hint}</span>}
        {right && <span className="ml-auto text-sm">{right}</span>}
      </div>
      {children}
    </section>
  )
}

export function Tile({ label, value, sub, tone = 'default' }: {
  label: string; value: React.ReactNode; sub?: React.ReactNode; tone?: 'default' | 'danger' | 'warn' | 'ok'
}) {
  const color = { default: 'text-slate-900', danger: 'text-rose-600', warn: 'text-amber-600', ok: 'text-emerald-600' }[tone]
  return (
    <div className="rounded-xl bg-white border border-slate-200 px-4 py-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`text-2xl font-bold tracking-tight mt-0.5 ${color}`}>{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  )
}

export function Fact({ label, value, tone = 'default' }: { label: string; value: React.ReactNode; tone?: 'default' | 'accent' }) {
  return (
    <span className={`inline-flex items-baseline gap-1.5 rounded-lg px-2.5 py-1 text-sm ${tone === 'accent' ? 'bg-indigo-50 text-indigo-800' : 'bg-slate-100 text-slate-700'}`}>
      <span className="text-xs opacity-70">{label}</span><b className="font-semibold">{value}</b>
    </span>
  )
}

export function Chip({ children, tone = 'gray' }: { children: React.ReactNode; tone?: 'gray' | 'blue' | 'amber' | 'red' | 'green' }) {
  const t = {
    gray: 'bg-slate-100 text-slate-600', blue: 'bg-indigo-50 text-indigo-700', amber: 'bg-amber-50 text-amber-800',
    red: 'bg-rose-50 text-rose-700', green: 'bg-emerald-50 text-emerald-700',
  }[tone]
  return <span className={`inline-block rounded-md px-2 py-0.5 text-xs ${t}`}>{children}</span>
}

/** 최근 며칠 게시량 막대. 막대 색은 그날의 상태 단계. */
export function Spark({ days, height = 32, barWidth = 10 }: {
  days: { day: string; count: number; level: Level }[]; height?: number; barWidth?: number
}) {
  const max = Math.max(...days.map(d => d.count), 1)
  return (
    <div className="flex items-end gap-[3px]" style={{ height }} aria-label="최근 게시량">
      {days.map(d => (
        <div key={d.day} title={`${d.day} · ${d.count}건 · ${LEVEL_META[d.level].label}`}
             style={{ width: barWidth, height: Math.max(2, Math.round((d.count / max) * height)), background: LEVEL_META[d.level].bar }}
             className="rounded-[2px]" />
      ))}
    </div>
  )
}

export function Card({ children, className = '', level }: { children: React.ReactNode; className?: string; level?: Level }) {
  const edge = level ? LEVEL_META[level].ring : 'border-slate-200'
  return <div className={`rounded-xl bg-white border ${edge} ${level === 'strong' || level === 'issue' ? 'border-2' : ''} ${className}`}>{children}</div>
}

export function Fold({ title, hint, children, open = false }: { title: string; hint?: React.ReactNode; children: React.ReactNode; open?: boolean }) {
  return (
    <details open={open} className="group border-t border-slate-100 first:border-t-0">
      <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-2.5 text-sm text-slate-600 hover:bg-slate-50">
        <span className="text-slate-400 transition-transform group-open:rotate-90">›</span>
        <span className="font-medium">{title}</span>
        {hint && <span className="text-xs text-slate-400">{hint}</span>}
      </summary>
      <div className="px-4 pb-3 pt-1">{children}</div>
    </details>
  )
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl border border-dashed border-slate-300 px-4 py-8 text-center text-sm text-slate-400">{children}</div>
}

export function GhostLink({ href, children }: { href: string; children: React.ReactNode }) {
  return <Link href={href} className="inline-flex items-center rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50">{children}</Link>
}
