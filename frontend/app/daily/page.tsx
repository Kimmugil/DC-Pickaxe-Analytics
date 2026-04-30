import Link from 'next/link'
import { api } from '@/lib/api'

function fmtDate(d: string) {
  const dt = new Date(d)
  return `${dt.getFullYear()}년 ${dt.getMonth() + 1}월 ${dt.getDate()}일`
}

export default async function DailyListPage() {
  let dates: string[] = []
  try { dates = await api.dailyDates() } catch {}

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link href="/" className="text-gray-400 hover:text-white text-sm">← 홈</Link>
          <h1 className="text-sm font-semibold">일간 체크포인트 목록</h1>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-6">
        {dates.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">데이터 없음</p>
        ) : (
          <div className="space-y-1">
            {dates.map(d => (
              <Link
                key={d}
                href={`/daily/${d}`}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors"
              >
                <span className="font-medium text-sm">{fmtDate(d)}</span>
                <span className="text-gray-400 text-xs">→</span>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
