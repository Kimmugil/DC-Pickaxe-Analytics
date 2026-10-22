import { db } from '@/lib/db'
import { AddRuleForm } from '@/components/AdminForms'
import { Card, Chip, PageHeader, Section } from '@/components/kit'
import { addRule, ruleAction, saveOverstatement } from '../actions'

export const dynamic = 'force-dynamic'

const DEFAULT_MAP: Record<string, string> = {
  '폭발적으로': '크게', '폭발적인': '큰', '폭발적': '큰', '폭증': '급증', '폭주': '급증', '폭발': '급증', '대혼란': '혼란', '아수라장': '혼란',
  '참사': '문제', '붕괴': '저하', '발칵': '논란', '난리': '논란', '극심한': '큰', '극심하게': '크게', '맹비난': '비판', '격분': '불만', '분노가 치솟': '불만이 커지',
}

type Rule = { id: number; pattern: string; note: string | null; enabled: boolean; hits: number | null }

export default async function Rules() {
  const sql = db()
  let list: Rule[]
  try {   // 규칙이 Postgres 정규식으로 해석될 때만 '최근 30일 해당 건수'를 셀 수 있음
    list = (await sql`
      select n.id, n.pattern, n.note, n.enabled,
        (select count(*)::int from posts p where p.posted_at > now() - interval '30 days' and p.source = 'live' and p.title ~* n.pattern) as hits
      from noise_rules n order by n.id`) as unknown as Rule[]
  } catch {
    list = (await sql`select id, pattern, note, enabled from noise_rules order by id`).map(r => ({ ...r, hits: null })) as unknown as Rule[]
  }
  const [m] = await sql`select value from settings where key = 'ai.overstatement_map'`
  let custom: Record<string, string> = {}
  try { custom = m?.value ? JSON.parse(m.value) : {} } catch { /* 잘못된 값은 무시 */ }
  const merged = { ...DEFAULT_MAP, ...custom }
  return (
    <div>
      <PageHeader title="규칙" sub="분석 결과를 다듬는 두 가지 규칙입니다" />

      <Section title="반복글 판별" hint="제목이 규칙에 맞으면 ‘반복글’로 표시해 이슈 점수·키워드·AI 요약에서 뺍니다 (삭제 아님)">
        <Card className="divide-y divide-slate-100">
          {list.map(r => (
            <div key={r.id} className="flex flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 text-sm">
              <code className={`min-w-48 flex-1 break-all font-mono text-xs ${r.enabled ? 'text-slate-800' : 'text-slate-400 line-through'}`}>{r.pattern}</code>
              {r.note && <span className="text-xs text-slate-400">{r.note}</span>}
              <Chip tone={r.hits ? 'blue' : 'gray'}>최근 30일 해당 {r.hits ?? '?'}건</Chip>
              <form action={ruleAction} className="flex gap-1.5">
                <input type="hidden" name="rule_id" value={r.id} />
                <button name="act" value="toggle" className="btn-ghost !py-1">{r.enabled ? '끄기' : '켜기'}</button>
                <button name="act" value="delete" className="btn-danger !py-1">삭제</button>
              </form>
            </div>
          ))}
          {!list.length && <p className="px-4 py-6 text-center text-sm text-slate-400">등록된 규칙이 없습니다.</p>}
        </Card>
        <div className="mt-3"><AddRuleForm action={addRule} /></div>
        <p className="mt-2 text-xs text-slate-500">새로 수집되는 글부터 적용됩니다.</p>
      </Section>

      <Section title="AI 과장 표현 순화" hint="AI가 쓴 요약에서 왼쪽 표현을 오른쪽으로 자동 치환합니다 (다음 분석부터 적용)">
        <form action={saveOverstatement} className="card space-y-3 p-4">
          <label className="label" htmlFor="map">한 줄에 하나 · 형식: <code>원문 =&gt; 대체어</code></label>
          <textarea id="map" name="map" rows={12} className="input font-mono" defaultValue={Object.entries(merged).map(([k, v]) => `${k} => ${v}`).join('\n')} />
          <button className="btn">저장</button>
        </form>
      </Section>
    </div>
  )
}
