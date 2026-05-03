'use client'
import { useState } from 'react'
import Link from 'next/link'

type State = 'locked' | 'unlocked'
type ActionStatus = 'idle' | 'running' | 'done' | 'error'

function StatusMsg({ status, msg }: { status: ActionStatus; msg: string }) {
  if (!msg) return null
  return (
    <p className={`text-xs mt-3 leading-relaxed ${status === 'error' ? 'text-red-500' : 'text-green-600'}`}>
      {msg}
    </p>
  )
}

export default function AdminPage() {
  const [state, setState]             = useState<State>('locked')
  const [password, setPassword]       = useState('')
  const [authError, setAuthError]     = useState(false)
  const [authLoading, setAuthLoading] = useState(false)

  // 전체 재분석 백필
  const [reanalyzeStatus, setReanalyzeStatus] = useState<ActionStatus>('idle')
  const [reanalyzeMsg, setReanalyzeMsg]       = useState('')
  const [startDate, setStartDate] = useState('2026-04-01')
  const [endDate, setEndDate]     = useState('2026-04-30')
  const [galleryId, setGalleryId] = useState('')
  const [dryRun, setDryRun]       = useState(false)

  // 주간 백필
  const [weeklyStatus, setWeeklyStatus] = useState<ActionStatus>('idle')
  const [weeklyMsg, setWeeklyMsg]       = useState('')
  const [weeklyStart, setWeeklyStart]   = useState('2026-01-05')
  const [weeklyEnd, setWeeklyEnd]       = useState('2026-04-28')
  const [weeklyDryRun, setWeeklyDryRun] = useState(false)

  // 월간 백필
  const [monthlyStatus, setMonthlyStatus] = useState<ActionStatus>('idle')
  const [monthlyMsg, setMonthlyMsg]       = useState('')
  const [monthlyStart, setMonthlyStart]   = useState('2026-01')
  const [monthlyEnd, setMonthlyEnd]       = useState('2026-04')
  const [monthlyDryRun, setMonthlyDryRun] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setAuthLoading(true)
    setAuthError(false)
    try {
      const res = await fetch('/api/admin/trigger-backfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, __auth_check_only: true }),
      })
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

  async function handleMonthlyBackfill() {
    if (!monthlyStart || !monthlyEnd) return
    setMonthlyStatus('running')
    setMonthlyMsg('')
    try {
      const res = await fetch('/api/admin/trigger-backfill-monthly', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, start_month: monthlyStart, end_month: monthlyEnd, dry_run: monthlyDryRun }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setMonthlyMsg(data.error ?? `오류 (${res.status})`)
        setMonthlyStatus('error')
      } else {
        setMonthlyStatus('done')
        setMonthlyMsg(`${monthlyDryRun ? '[dry-run] ' : ''}${monthlyStart} ~ ${monthlyEnd} 월간 백필 작업이 GitHub Actions에서 시작됐습니다.`)
      }
    } catch (err: unknown) {
      setMonthlyMsg(String(err))
      setMonthlyStatus('error')
    }
  }

  async function handleWeeklyBackfill() {
    if (!weeklyStart || !weeklyEnd) return
    setWeeklyStatus('running')
    setWeeklyMsg('')
    try {
      const res = await fetch('/api/admin/trigger-backfill-weekly', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, start_date: weeklyStart, end_date: weeklyEnd, dry_run: weeklyDryRun }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setWeeklyMsg(data.error ?? `오류 (${res.status})`)
        setWeeklyStatus('error')
      } else {
        setWeeklyStatus('done')
        setWeeklyMsg(`${weeklyDryRun ? '[dry-run] ' : ''}${weeklyStart} ~ ${weeklyEnd} 주간 백필 작업이 GitHub Actions에서 시작됐습니다.`)
      }
    } catch (err: unknown) {
      setWeeklyMsg(String(err))
      setWeeklyStatus('error')
    }
  }

  async function handleReanalyze() {
    if (!startDate || !endDate) return
    setReanalyzeStatus('running')
    setReanalyzeMsg('')
    try {
      const res = await fetch('/api/admin/trigger-reanalyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password, start_date: startDate, end_date: endDate, gallery_id: galleryId || undefined, dry_run: dryRun }),
      })
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setReanalyzeMsg(data.error ?? `오류 (${res.status})`)
        setReanalyzeStatus('error')
      } else {
        setReanalyzeStatus('done')
        setReanalyzeMsg(`${dryRun ? '[dry-run] ' : ''}${startDate} ~ ${endDate} 재분석 작업이 GitHub Actions에서 시작됐습니다. 완료까지 수십 분이 소요될 수 있습니다.`)
      }
    } catch (err: unknown) {
      setReanalyzeMsg(String(err))
      setReanalyzeStatus('error')
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
              {authError && <p className="text-xs text-red-500">비밀번호가 틀렸습니다.</p>}
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

            {/* ── 전체 재분석 백필 (v2) ── */}
            <div className="bg-white border border-blue-100 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">전체 재분석 백필 <span className="text-[11px] text-blue-500 font-normal ml-1">v2 — 본문 포함</span></h2>
              <p className="text-xs text-gray-400 mb-4 leading-relaxed">
                지정 기간의 갤러리 데이터를 갤러리 시트에서 다시 읽어 새 AI 분석 구조(본문 샘플·카테고리 점수·주요 이슈)로 완전 재처리합니다.
                기존 daily_issues 행은 덮어씁니다. 수십 분 소요.
              </p>

              <div className="space-y-2 mb-4">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="text-[11px] text-gray-400 block mb-1">시작 날짜</label>
                    <input
                      type="date"
                      value={startDate}
                      onChange={e => setStartDate(e.target.value)}
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-[11px] text-gray-400 block mb-1">종료 날짜</label>
                    <input
                      type="date"
                      value={endDate}
                      onChange={e => setEndDate(e.target.value)}
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">갤러리 ID <span className="text-gray-300">(비워두면 전체)</span></label>
                  <input
                    type="text"
                    value={galleryId}
                    onChange={e => setGalleryId(e.target.value)}
                    placeholder="예: maplestory_mobile"
                    className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                  />
                </div>
                <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={dryRun}
                    onChange={e => setDryRun(e.target.checked)}
                    className="rounded"
                  />
                  dry-run (실제 쓰기 없이 대상 목록만 출력)
                </label>
              </div>

              <button
                onClick={handleReanalyze}
                disabled={reanalyzeStatus === 'running' || !startDate || !endDate}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-sm px-4 py-2 rounded transition-colors"
              >
                {reanalyzeStatus === 'running' ? '실행 중...' : '재분석 백필 실행'}
              </button>
              <StatusMsg status={reanalyzeStatus} msg={reanalyzeMsg} />
            </div>

            {/* ── 주간 백필 ── */}
            <div className="bg-white border border-green-100 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">주간 분석 백필 <span className="text-[11px] text-green-600 font-normal ml-1">weekly</span></h2>
              <p className="text-xs text-gray-400 mb-4 leading-relaxed">
                지정 기간의 모든 주(월요일 기준)를 순서대로 분석해 weekly_galleries / weekly_overall 시트에 적재합니다.
              </p>

              <div className="space-y-2 mb-4">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="text-[11px] text-gray-400 block mb-1">시작 날짜</label>
                    <input
                      type="date"
                      value={weeklyStart}
                      onChange={e => setWeeklyStart(e.target.value)}
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-[11px] text-gray-400 block mb-1">종료 날짜</label>
                    <input
                      type="date"
                      value={weeklyEnd}
                      onChange={e => setWeeklyEnd(e.target.value)}
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={weeklyDryRun}
                    onChange={e => setWeeklyDryRun(e.target.checked)}
                    className="rounded"
                  />
                  dry-run (실제 쓰기 없이 대상 목록만 출력)
                </label>
              </div>

              <button
                onClick={handleWeeklyBackfill}
                disabled={weeklyStatus === 'running' || !weeklyStart || !weeklyEnd}
                className="bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white text-sm px-4 py-2 rounded transition-colors"
              >
                {weeklyStatus === 'running' ? '실행 중...' : '주간 백필 실행'}
              </button>
              <StatusMsg status={weeklyStatus} msg={weeklyMsg} />
            </div>

            {/* ── 월간 백필 ── */}
            <div className="bg-white border border-purple-100 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">월간 분석 백필 <span className="text-[11px] text-purple-600 font-normal ml-1">monthly</span></h2>
              <p className="text-xs text-gray-400 mb-4 leading-relaxed">
                daily_issues 탭에서 기간 내 데이터를 읽어 월별로 집계하고 AI 요약을 생성해 monthly_issues / monthly_overall 시트에 적재합니다.
              </p>

              <div className="space-y-2 mb-4">
                <div className="flex gap-2">
                  <div className="flex-1">
                    <label className="text-[11px] text-gray-400 block mb-1">시작 월 (YYYY-MM)</label>
                    <input
                      type="month"
                      value={monthlyStart}
                      onChange={e => setMonthlyStart(e.target.value)}
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                    />
                  </div>
                  <div className="flex-1">
                    <label className="text-[11px] text-gray-400 block mb-1">종료 월 (YYYY-MM)</label>
                    <input
                      type="month"
                      value={monthlyEnd}
                      onChange={e => setMonthlyEnd(e.target.value)}
                      className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs outline-none focus:border-gray-400"
                    />
                  </div>
                </div>
                <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={monthlyDryRun}
                    onChange={e => setMonthlyDryRun(e.target.checked)}
                    className="rounded"
                  />
                  dry-run (실제 쓰기 없이 대상 목록만 출력)
                </label>
              </div>

              <button
                onClick={handleMonthlyBackfill}
                disabled={monthlyStatus === 'running' || !monthlyStart || !monthlyEnd}
                className="bg-purple-700 hover:bg-purple-600 disabled:opacity-40 text-white text-sm px-4 py-2 rounded transition-colors"
              >
                {monthlyStatus === 'running' ? '실행 중...' : '월간 백필 실행'}
              </button>
              <StatusMsg status={monthlyStatus} msg={monthlyMsg} />
            </div>

            {/* ── 캐시 초기화 ── */}
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

            {/* ── GitHub Actions ── */}
            <div className="bg-white border border-gray-200 rounded-lg p-5">
              <h2 className="text-sm font-semibold text-gray-900 mb-1">GitHub Actions</h2>
              <p className="text-xs text-gray-400 mb-3">진행 상황 확인 및 직접 워크플로우 관리.</p>
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
