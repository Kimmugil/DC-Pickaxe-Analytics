import { notFound } from 'next/navigation'
import { getWeeklyByWeek } from '@/lib/data'
import { getTexts } from '@/lib/texts'
import { Nav } from '@/components/Nav'
import { WeeklyGalleryFilter } from '@/components/WeeklyGalleryCard'

interface Props { params: Promise<{ week: string }> }

function fmt(d: string) {
  if (!d) return ''
  const [, m, day] = d.split('-').map(Number)
  return `${m}월 ${day}일`
}

export default async function WeeklyDetailPage({ params }: Props) {
  const { week } = await params

  const [t, data] = await Promise.all([
    getTexts(),
    getWeeklyByWeek(week).catch(() => null),
  ])

  if (!data) notFound()

  const { galleries, overall } = data
  const sorted = [...galleries].sort((a, b) => b.total_posts - a.total_posts)

  const suffix = t['weekly_detail.page_title_suffix'] ?? '주간 리포트'
  const titleStr = overall.week_start
    ? `${fmt(overall.week_start)} ~ ${fmt(overall.week_end ?? week)} ${suffix}`
    : `${week} ${suffix}`

  return (
    <div className="min-h-screen bg-gray-50">
      <Nav
        back={{ href: '/reports', label: t['nav.reports'] ?? '종합 리포트' }}
        title={titleStr}
        subtitle={`${galleries.length}개 갤러리`}
      />

      <main className="max-w-5xl mx-auto px-4 py-6 space-y-6">

        {/* 전체 종합 요약 */}
        {overall.ai_summary && (
          <section className="bg-white border border-gray-200 rounded-lg p-5">
            <h2 className="text-xs text-gray-400 font-medium mb-3">
              {t['weekly_detail.summary_title'] ?? '종합 요약'}
            </h2>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-line">
              {overall.ai_summary}
            </p>
          </section>
        )}

        {/* 갤러리별 카드 + 카테고리 필터 */}
        <WeeklyGalleryFilter galleries={sorted} t={t} />

      </main>
    </div>
  )
}
