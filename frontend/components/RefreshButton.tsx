'use client'
import { useState } from 'react'

export function RefreshButton() {
  const [state, setState] = useState<'idle' | 'loading' | 'done'>('idle')

  async function handleClick() {
    setState('loading')
    try {
      await fetch('/api/revalidate', { method: 'POST' })
      setState('done')
      setTimeout(() => {
        window.location.reload()
      }, 300)
    } catch {
      setState('idle')
    }
  }

  return (
    <button
      onClick={handleClick}
      disabled={state !== 'idle'}
      title="구글시트 동기화"
      className="fixed bottom-5 right-5 z-50 w-10 h-10 bg-gray-800 hover:bg-gray-700 disabled:opacity-40 text-white rounded-full shadow-lg flex items-center justify-center transition-colors text-base"
    >
      {state === 'loading' ? (
        <span className="animate-spin inline-block">↻</span>
      ) : state === 'done' ? '✓' : '↻'}
    </button>
  )
}
