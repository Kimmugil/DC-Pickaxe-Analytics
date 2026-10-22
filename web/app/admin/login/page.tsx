'use client'
import { useActionState } from 'react'
import { login } from './actions'

export default function LoginPage() {
  const [state, action, pending] = useActionState(login, { error: '' })
  return (
    <div className="mx-auto mt-16 max-w-sm">
      <div className="mb-6 text-center">
        <div className="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-xl bg-slate-900 text-xl text-white">⛏</div>
        <h1 className="text-xl font-bold text-slate-900">관리자 로그인</h1>
        <p className="mt-1 text-sm text-slate-500">관리자만 들어올 수 있는 공간입니다</p>
      </div>
      <form action={action} className="card space-y-4 p-5">
        <div>
          <label className="label" htmlFor="pw">비밀번호</label>
          <input id="pw" name="password" type="password" autoComplete="current-password" className="input" autoFocus required />
        </div>
        {state.error && <p role="alert" className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{state.error}</p>}
        <button className="btn w-full" disabled={pending}>{pending ? '확인 중…' : '로그인'}</button>
        <p className="text-center text-xs text-slate-400">비밀번호를 5번 틀리면 15분 동안 잠깁니다</p>
      </form>
    </div>
  )
}
