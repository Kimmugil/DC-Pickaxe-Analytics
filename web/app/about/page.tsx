import { Card, Chip, PageHeader, Section, StatusPill } from '@/components/kit'
import { getTexts, T } from '@/lib/texts'

export const dynamic = 'force-dynamic'

const PARTS = [
  ['게시량 급증', '0~4점', '같은 요일 4주 중앙값(없으면 7일 중앙값)과 비교한 그날 게시량의 배수와 증가량입니다. 같은 제목이 하루 8번 이상 반복되면 묶어서 5건까지만 셉니다.'],
  ['단일 글 화제성', '0~3점', '그날 댓글이 가장 많은 글이, 이 갤러리의 평소 하루 최다 댓글(최근 28일 중앙값)의 몇 배인지 봅니다. 글이 5개 미만이거나 최다 댓글이 10개 미만이면 계산하지 않습니다.'],
  ['화제 글 수', '0~3점', '평소 상위 1% 수준의 댓글을 받은 글이 기대한 수의 몇 배인지 봅니다.'],
  ['모멘텀', '+1점', '최근 3일 평균도 기준선보다 30% 이상 높을 때 더합니다.'],
  ['개념글', '+1점', '개념글 수가 평소 중앙값의 2배 이상(3개 이상)일 때 더합니다.'],
]

export default async function About() {
  const t = await getTexts()
  return (
    <div className="max-w-3xl">
      <PageHeader title={T(t, 'about.title')} sub={T(t, 'about.sub')} />

      <Section title="상태 단계">
        <Card className="divide-y divide-slate-100">
          {([['strong', '평소보다 훨씬 크게 달랐던 날. 새 방식 기준 6점 이상.'], ['issue', '평소와 확연히 달랐던 날. 3점 이상.'], ['watch', '이슈 직전. 2점. 짧은 요약만 붙습니다.'], ['normal', '평소 수준.']] as const).map(([l, d]) => (
            <div key={l} className="flex items-center gap-4 px-4 py-3 text-sm"><StatusPill level={l} className="w-20 justify-center" /><span className="text-slate-600">{d}</span></div>
          ))}
        </Card>
        <p className="mt-2 text-xs text-slate-500">활발한 갤러리에서 이슈가 너무 자주 잡히면 기준을 자동으로 높이고, 갤러리마다 관리자가 기준을 조절할 수 있습니다. 규모가 다른 갤러리를 같은 잣대로 재지 않기 위해 모든 항목을 그 갤러리 자신의 최근 28일 기록과 비교합니다.</p>
      </Section>

      <Section title="점수 구성" hint="합계는 최대 10점">
        <div className="space-y-2">
          {PARTS.map(([h, p, d]) => (
            <Card key={h} className="px-4 py-3"><div className="flex items-center gap-2"><b className="text-sm">{h}</b><Chip>{p}</Chip></div><p className="mt-1 text-sm text-slate-600">{d}</p></Card>
          ))}
        </div>
      </Section>

      <Section title="알아두실 점">
        <Card className="px-5 py-4">
          <ul className="list-disc space-y-1.5 pl-4 text-sm leading-relaxed text-slate-700">
            <li>글의 댓글·조회·추천 수는 올라온 뒤 12시간, 36시간 시점에 다시 읽어 갱신합니다. 분석은 숫자가 안정된 뒤에 합니다.</li>
            <li>요약과 이슈 정리는 AI(Gemini)가 작성합니다. 근거가 약한 이슈는 접어서 보여주고 과장 표현은 자동으로 순화하지만, 부정확할 수 있으니 근거 글 링크를 함께 확인해 주세요.</li>
            <li>욕설은 ‘주제 키워드’ 순위에서만 제외하며 감정의 세기를 판단하는 데 쓰지 않습니다.</li>
            <li>같은 제목이 반복된 도배성 글은 점수 영향을 제한하되 그 사실은 리포트에 남깁니다.</li>
            <li>작성자(닉네임·IP)는 분석에 쓰지 않습니다.</li>
            <li>‘예전 방식 점수’ 표시가 붙은 날은 이전 시스템의 기준(숫자가 낮게 고정된 데이터)으로 계산된 기록이라 새 기준과 직접 비교할 수 없습니다.</li>
          </ul>
        </Card>
      </Section>
    </div>
  )
}
