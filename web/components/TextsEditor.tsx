'use client'
import { useState } from 'react'

type Row = { key: string; label: string; def: string; group: string; value: string }

/** 화면 문구 편집기: 묶음별로 보여주고 검색할 수 있다. 바꾼 문구는 '기본값과 다름' 표시가 붙는다. */
export function TextsEditor({ rows, action }: { rows: Row[]; action: (f: FormData) => Promise<void> }) {
  const [q, setQ] = useState('')
  const [vals, setVals] = useState<Record<string, string>>(Object.fromEntries(rows.map(r => [r.key, r.value])))
  const groups = new Map<string, Row[]>()
  for (const r of rows) groups.set(r.group, [...(groups.get(r.group) ?? []), r])
  const match = (r: Row) => !q || r.label.includes(q) || r.key.includes(q) || (vals[r.key] ?? '').includes(q)
  return (
    <form action={action}>
      <div className="sticky top-14 z-10 mb-4 flex items-center gap-3 rounded-xl border border-slate-200 bg-white/95 px-4 py-2.5 backdrop-blur">
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="문구 이름이나 내용으로 검색" className="input !w-64" aria-label="검색" />
        <span className="text-xs text-slate-400">{rows.filter(match).length}개 표시</span>
        <button className="btn ml-auto">전체 저장</button>
      </div>
      <div className="space-y-4">
        {[...groups.entries()].map(([g, list]) => (
          <div key={g} className={`overflow-hidden rounded-xl border border-slate-200 bg-white ${list.some(match) ? '' : 'hidden'}`}>
            <div className="border-b border-slate-100 bg-slate-50 px-4 py-2 text-xs font-semibold text-slate-600">{g}</div>
            <div className="divide-y divide-slate-100">
              {list.map(r => {
                const changed = (vals[r.key] ?? '') !== r.def
                return (
                  <div key={r.key} className={`px-4 py-3 ${match(r) ? '' : 'hidden'}`}>
                    <div className="mb-1 flex items-baseline gap-2">
                      <label htmlFor={`ui.${r.key}`} className="text-sm font-medium text-slate-800">{r.label}</label>
                      {changed && <span className="rounded bg-indigo-50 px-1.5 text-[11px] text-indigo-700">기본값과 다름</span>}
                      <span className="ml-auto font-mono text-[11px] text-slate-300">{r.key}</span>
                    </div>
                    <input id={`ui.${r.key}`} name={`ui.${r.key}`} value={vals[r.key] ?? ''} onChange={e => setVals(v => ({ ...v, [r.key]: e.target.value }))} className="input" />
                    {changed && <button type="button" onClick={() => setVals(v => ({ ...v, [r.key]: r.def }))} className="mt-1 text-xs text-slate-500 hover:underline">기본값으로 되돌리기: {r.def}</button>}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </form>
  )
}
