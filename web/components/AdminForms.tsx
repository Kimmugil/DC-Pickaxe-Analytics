'use client'
import { useActionState } from 'react'

type Action = (prev: { ok: boolean; msg: string }, f: FormData) => Promise<{ ok: boolean; msg: string }>
const init = { ok: true, msg: '' }

function Msg({ s }: { s: { ok: boolean; msg: string } }) {
  return s.msg ? <p className={`text-sm ${s.ok ? 'text-emerald-700' : 'text-red-600'}`}>{s.msg}</p> : null
}

export function AddGalleryForm({ action }: { action: Action }) {
  const [state, run, pending] = useActionState(action, init)
  return (
    <form action={run} className="card space-y-3">
      <h2 className="font-semibold text-sm">갤러리 추가</h2>
      <div className="grid sm:grid-cols-4 gap-3">
        <div><label className="label">갤러리 ID (주소의 id=…)</label><input name="gallery_id" className="input" placeholder="projectcc" required /></div>
        <div><label className="label">표시 이름 (비우면 자동)</label><input name="name" className="input" placeholder="쿠키런 크럼블" /></div>
        <div><label className="label">종류</label>
          <select name="type" className="input" defaultValue="auto">
            <option value="auto">자동 판별</option><option value="minor">마이너</option><option value="major">일반</option><option value="mini">미니</option>
          </select></div>
        <div className="flex items-end"><button className="btn w-full" disabled={pending}>{pending ? '확인 중…' : '추가'}</button></div>
      </div>
      <Msg s={state} />
    </form>
  )
}

export function AddRuleForm({ action }: { action: Action }) {
  const [state, run, pending] = useActionState(action, init)
  return (
    <form action={run} className="card space-y-3">
      <h2 className="font-semibold text-sm">반복글 규칙 추가</h2>
      <div className="grid sm:grid-cols-3 gap-3">
        <div className="sm:col-span-2"><label className="label">제목에 이 패턴이 있으면 반복글(쿠폰·교환 등)로 표시 — 정규식, 예: 코드\s*교환|쿠폰</label><input name="pattern" className="input font-mono" required /></div>
        <div><label className="label">메모</label><input name="note" className="input" /></div>
      </div>
      <div className="flex items-center gap-3"><button className="btn" disabled={pending}>추가</button><Msg s={state} /></div>
    </form>
  )
}
