import type { DailyIssue } from '@/types'
import { notFound } from 'next/navigation'
import { getDailyByDate } from '@/lib/data'
import { getTexts, tp } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { DailyDetailFilter } from '@/components/DailyDetailFilter'

interface Props { params: Promise<{ date: string }> }

function fmt(d: string) {
  if (!d) return ''
  const [y, m, day] = d.split('-').map(Number)
  return `${y}년 ${m}월 ${day}일`
}

export default async function DailyDetailPage({ params }: Props) {
  const { date } = await params

  const [t, issues] = await Promise.all([
    getTexts(),
    getDailyByDate(date).catch(() => null),
  ])

  if (issues === null) notFound()

  const sorted = [...issues].sort((a, b) => b.issue_score - a.issue_score)
  const issueList  = sorted.filter(i => i.has_issue)
  const borderList = sorted.filter(i => !i.has_issue && i.is_borderline)
  const normalList = sorted.filter(i => !i.has_issue && !i.is_borderline)

  const pageTitle   = `${fmt(date)} ${t['daily_detail.page_title_suffix'] ?? '일간 체크포인트'}`
  const pageSubtitle = issueList.length > 0
    ? tp(t, 'daily_detail.issue_detected', { count: issueList.length }, '이슈 {count}개 갤러리 감지')
    : undefined

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav back={{ href: '/daily', label: t['nav.daily'] ?? '일간 이슈' }} title={pageTitle} subtitle={pageSubtitle} />

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">

        {(issueList.length > 0 || borderList.length > 0) && (
          <DailyDetailFilter
            issueList={issueList}
            borderList={borderList}
            t={t}
            labels={{
              sectionIssue:      t['daily_detail.section_issue']      ?? '이슈 갤러리',
              sectionBorderline: t['daily_detail.section_borderline'] ?? '주목 갤러리 (경계)',
            }}
          />
        )}

        {normalList.length > 0 && (
          <section>
            <h2 className="text-xs text-gray-400 font-medium mb-2">
              {t['daily_detail.section_normal'] ?? '정상 갤러리'}
            </h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {normalList.map(i => (
                <div
                  key={i.gallery_id}
                  className="bg-white border border-gray-200 rounded-lg px-3 py-2 flex items-center justify-between"
                >
                  <span className="text-sm text-gray-700 truncate">{i.gallery_name}</span>
                  <span className="text-xs text-gray-400 font-medium tabular-nums ml-2 shrink-0">
                    {i.posts_total}건
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {issues.length === 0 && (
          <div className="text-center py-20 text-gray-400 text-sm">
            {t['common.no_data'] ?? '데이터 없음'}
          </div>
        )}
      </main>
    </div>
  )
}
