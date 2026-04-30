import Link from 'next/link'
import { getWeeklyList } from '@/lib/data'

function fmtDate(d: string) {
  const dt = new Date(d)
  return `${dt.getMonth() + 1}월 ${dt.getDate()}일`
}

export default async function WeeklyListPage() {
  let weeks: string[] = []
  try { weeks = await getWeeklyList() } catch {}

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-gray-900 text-white">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center gap-3">
          <Link href="/" className="text-gray-400 hover:text-white text-sm">← 홈</Link>
          <h1 className="text-sm font-semibold">주간 리포트 목록</h1>
        </div>
      </header>
      <main className="max-w-4xl mx-auto px-4 py-6">
        {weeks.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">데이터 없음</p>
        ) : (
          <div className="space-y-1">
            {weeks.map(ws => {
              const we = new Date(ws)
              we.setDate(we.getDate() + 6)
              const weStr = we.toISOString().slice(0, 10)
              return (
                <Link
                  key={ws}
                  href={`/weekly/${ws}`}
                  className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors"
                >
                  <span className="font-medium text-sm">{fmtDate(ws)} ~ {fmtDate(weStr)}</span>
                  <span className="text-gray-400 text-xs">→</span>
                </Link>
              )
            })}
          </div>
        )}
      </main>
    </div>
  )
}
