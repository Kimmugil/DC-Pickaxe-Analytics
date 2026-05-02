'use client'
import { useState } from 'react'
import Link from 'next/link'

type State = 'locked' | 'unlocked'
type BackfillStatus = 'idle' | 'running' | 'done' | 'error'

export default function AdminPage() {
  const [state, setState]           = useState<State>('locked')
  const [password, setPassword]     = useState('')
  const [authError, setAuthError]   = useState(false)
  const [authLoading, setAuthLoading] = useState(false)
  const [backfillStatus, setBackfillStatus] = useState<BackfillStatus>('idle')
  const [backfillMsg, setBackfillMsg] = useState('')

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError(false)
    try {
      const res = await fetch('/api/admin/trigger-backfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // 비밀번호 검증만 하되 backfill은 안 트리거 — dry_run으로 auth만 확인
        body: JSON.stringify({ password, __auth_check_only: true }),
      })
      // 401이면 틀린 비밀번호, 그 외는 맞은 것으로 처리
      if (res.status === 401) {
        setAuthError(true)
      } else {
        setState('unlocked')
      }
    } catch {
      setAuthError(true)
    } finally {
      setAuthLoading(false)
    }
  }

  async function handleBackfill() {
    setBackfillStatus('running')
    setBackfillMsg('')
    try {
      const res = await fetch('/api/admin/trigger-backfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setBackfillMsg(data.error ?? `오류 (${res.status})`)
        setBackfillStatus('error')
      } else {
        setBackfillStatus('done')
        setBackfillMsg('GitHub Actions에 백필 작업이 시작되었습니다. Actions 탭에서 진행 상황을 확인하세요.')
      }
    } catch (err: unknown) {
      setBackfillMsg(String(err))
      setBackfillStatus('error')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gray-900 text-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 h-12 flex items-center gap-4">
          <Link href="/" className="text-gray-400 hover:text-white text-sm transition-colors">← 홈</Link>
          <div className="border-l border-gray-700 pl-3">
            <p className="text-sm font-medium text-white">관리자 패널</p>
          </div>
        </div>
      </header>

      <main className="max-w-lg mx-auto px-4 py-12">
        {state === 'locked' ? (
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h1 className="text-sm font-semibold text-gray-900 mb-1">관리자 인증</h1>
            <p className="text-xs text-gray-400 mb-5">마스터 스프레드시트 config 탭의 비밀번호를 입력하세요.</p>

            <form onSubmit={handleLogin} className="space-y-3">
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="비밀번호"
                className="w-full border border-gray-200 rounded px-3 py-2 text-sm outline-none focus:border-gray-400 transition-colors"
                autoFocus
              />
              {authError && (
                <p className="text-xs text-red-500">비밀번호가 틀렸습니다.</p>
              )}
              <button
                type="submit"
                disabled={!password || authLoading}
                className="w-full bg-gray-900 hover:bg-gray-700 disabled:opacity-40 text-white text-sm py-2 rounded transition-colors"
              >
                {authLoading ? '확인 중...' : '확인'}
              </button>
            </form>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">과거 데이터 AI 태그 채우기</h2>
              <p className="text-xs text-gray-400 mb-4 leading-relaxed">
                daily_issues 시트에서 temperature_tag / issue_cause가 없는 이슈 행을 찾아
                Gemini AI로 재처리합니다. GitHub Actions를 통해 실행되며 완료까지 수분이 걸릴 수 있습니다.
              </p>

              <button
                onClick={handleBackfill}
                disabled={backfillStatus === 'running'}
                className="bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-white text-sm px-4 py-2 rounded transition-colors"
              >
                {backfillStatus === 'running' ? '실행 중...' : '백필 실행'}
              </button>

              {backfillMsg && (
                <p className={`text-xs mt-3 leading-relaxed ${backfillStatus === 'error' ? 'text-red-500' : 'text-green-600'}`}>
                  {backfillMsg}
                </p>
              )}
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">캐시 초기화</h2>
              <p className="text-xs text-gray-400 mb-4">
                구글시트 변경사항을 즉시 반영합니다. 우하단 ↻ 버튼과 동일한 기능입니다.
              </p>
              <button
                onClick={async () => {
                  await fetch('/api/revalidate', { method: 'POST' })
                  window.location.reload()
                }}
                className="bg-gray-800 hover:bg-gray-700 text-white text-sm px-4 py-2 rounded transition-colors"
              >
                캐시 초기화
              </button>
            </div>

            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">GitHub Actions</h2>
              <p className="text-xs text-gray-400 mb-3">직접 워크플로우를 관리하려면 GitHub에서 확인하세요.</p>
              <a
                href="https://github.com/Kimmugil/DC-Pickaxe-Analytics/actions"
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-500 hover:underline"
              >
                GitHub Actions 바로가기 →
              </a>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
