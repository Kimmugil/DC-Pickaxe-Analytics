import { db } from '@/lib/db'
import { SETTING_DEFS } from '@/lib/settingsDefs'
import { Card, PageHeader, Section } from '@/components/kit'
import { saveSettings } from '../actions'

export const dynamic = 'force-dynamic'

const GROUPS: [string, string, string][] = [
  ['analyzer.', '이슈 판정', '이슈·주목 기준과 도배 처리'],
  ['ai.', 'AI 요약', '모델과 사용량 상한, 비용 추정용 요금'],
  ['db.', 'DB', '현황의 사용률 표시용'],
  ['collector.', '수집', '수집 범위와 차단 대응'],
]

export default async function SettingsAdmin() {
  const rows = await db()`select key, value from settings where key = any(${SETTING_DEFS.map(d => d.key)})`
  const cur = Object.fromEntries(rows.map(r => [r.key as string, r.value as string]))
  return (
    <form action={saveSettings} className="max-w-3xl">
      <PageHeader title="설정" sub="기본값과 같거나 비워 두면 기본값을 씁니다. 바뀐 값은 다음 수집·분석 실행부터 적용됩니다"
        right={<button className="btn">저장</button>} />
      {GROUPS.map(([prefix, title, hint]) => (
        <Section key={prefix} title={title} hint={hint}>
          <Card className="divide-y divide-slate-100">
            {SETTING_DEFS.filter(d => d.key.startsWith(prefix)).map(d => (
              <div key={d.key} className="grid gap-3 px-4 py-3 sm:grid-cols-[1fr_10rem] sm:items-center">
                <div>
                  <label htmlFor={d.key} className="text-sm font-medium text-slate-800">{d.label}</label>
                  <p className="text-xs text-slate-500">{d.help} <span className="text-slate-400">(기본 {String(d.def)})</span></p>
                </div>
                <input id={d.key} name={d.key} defaultValue={cur[d.key] ?? String(d.def)} className="input" />
              </div>
            ))}
          </Card>
        </Section>
      ))}
      <button className="btn">저장</button>
    </form>
  )
}
