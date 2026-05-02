import Link from 'next/link'
import { getDailyIssueList } from '@/lib/data'
import { Nav } from '@/components/Nav'

function fmt(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

export default async function DailyListPage() {
  let list: Awaited<ReturnType<typeof getDailyIssueList>> = []
  try {
    list = await getDailyIssueList()
  } catch {}

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav
        back={{ href: '/reports', label: '리포트 목록' }}
        title="일간 이슈 목록"
      />

      <main className="max-w-4xl mx-auto px-4 py-6">
        {list.length === 0 ? (
          <p className="text-gray-400 text-sm text-center py-20">데이터 없음</p>
        ) : (
          <div className="space-y-1.5">
            {list.map(item => (
              <Link
                key={item.date}
                href={`/daily/${item.date}`}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg px-4 py-3 hover:border-gray-300 transition-colors group"
              >
                <div className="min-w-0">
                  <span className="text-sm font-medium text-gray-900">{fmt(item.date)}</span>
                  {item.top_galleries.length > 0 && (
                    <div className="flex items-center gap-3 mt-0.5 flex-wrap">
                      {item.top_galleries.map(g => (
                        <span key={g.name} className="text-xs text-gray-500">
                          {g.name}{' '}
                          <span className="tabular-nums text-gray-400">{g.score}점</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-3">
                  <span className="text-xs text-gray-400">
                    이슈 {item.issue_count}개
                    {item.borderline_count > 0 && ` · 경계 ${item.borderline_count}개`}
                  </span>
                  <span className="text-gray-300 group-hover:text-gray-500 text-sm transition-colors">
                    →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
