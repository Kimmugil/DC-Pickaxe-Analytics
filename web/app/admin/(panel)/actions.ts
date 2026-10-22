'use server'
import { revalidatePath } from 'next/cache'
import { requireAdmin } from '@/lib/auth'
import { db } from '@/lib/db'
import { SETTING_DEFS } from '@/lib/settingsDefs'
import { TEXT_DEFS } from '@/lib/textDefs'

const s = (f: FormData, k: string) => String(f.get(k) ?? '').trim()
const n = (f: FormData, k: string, lo: number, hi: number, def: number) => {
  const v = Number(f.get(k))
  return Number.isFinite(v) ? Math.min(hi, Math.max(lo, Math.round(v))) : def
}
const PREFIX: Record<string, string> = { minor: 'mgallery/board', major: 'board', mini: 'mini/board' }

/** 갤러리 종류 자동 판별: 마이너 → 일반 → 미니 순으로 목록 페이지가 열리는 곳 */
async function detectGallery(id: string): Promise<{ type: string; title: string } | null> {
  for (const type of ['minor', 'major', 'mini']) {
    try {
      const r = await fetch(`https://gall.dcinside.com/${PREFIX[type]}/lists/?id=${encodeURIComponent(id)}`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36', 'Accept-Language': 'ko-KR,ko;q=0.9' },
        cache: 'no-store', signal: AbortSignal.timeout(12000),
      })
      const html = await r.text()
      if (r.ok && /gall_list|listwrap2/.test(html)) {
        const t = /<title>([^<]*)<\/title>/.exec(html)?.[1] ?? ''
        return { type, title: t.replace(/\s*-\s*디시인사이드.*/, '').replace(/\s*(마이너|미니)?\s*갤러리\s*$/, '').trim() }
      }
    } catch { /* 다음 종류 시도 */ }
  }
  return null
}

export type Result = { ok: boolean; msg: string }

export async function addGallery(_p: Result, f: FormData): Promise<Result> {
  await requireAdmin()
  const id = s(f, 'gallery_id').toLowerCase()
  if (!/^[a-z0-9_]{2,40}$/.test(id)) return { ok: false, msg: '갤러리 ID 는 영문 소문자·숫자·_ 2~40자로 입력하세요.' }
  let type = s(f, 'type')
  let name = s(f, 'name')
  if (type === 'auto' || !name) {
    const d = await detectGallery(id)
    if (type === 'auto' && !d) return { ok: false, msg: '디시에서 이 갤러리를 찾지 못했습니다. ID가 맞는지, 또는 종류를 직접 선택해 보세요.' }
    if (type === 'auto' && d) type = d.type
    if (!name) name = d?.title || id
  }
  if (!['minor', 'major', 'mini'].includes(type)) return { ok: false, msg: '갤러리 종류가 올바르지 않습니다.' }
  const r = await db()`insert into galleries (gallery_id, name, gallery_type) values (${id}, ${name}, ${type}) on conflict do nothing returning gallery_id`
  revalidatePath('/admin/galleries')
  return r.length ? { ok: true, msg: `${name} (${type}) 추가됨. 다음 수집 때 자동으로 첫 수집이 시작되고, 과거 글은 '실행' 메뉴에서 채울 수 있습니다.` }
                  : { ok: false, msg: '이미 등록된 갤러리입니다.' }
}

export async function updateGallery(f: FormData) {
  await requireAdmin()
  const id = s(f, 'gallery_id')
  await db()`update galleries set
      name = ${s(f, 'name').slice(0, 60) || id},
      short_name = ${s(f, 'short_name').slice(0, 10) || null},
      is_active = ${f.get('is_active') === 'on'},
      collect_interval_min = ${n(f, 'collect_interval_min', 15, 1440, 60)},
      issue_threshold_adjust = ${n(f, 'issue_threshold_adjust', -2, 3, 0)},
      min_issue_posts = ${n(f, 'min_issue_posts', 0, 1000, 0)},
      notes = ${s(f, 'notes').slice(0, 2000) || null}
    where gallery_id = ${id}`
  revalidatePath('/admin/galleries')
  revalidatePath('/gallery')
  revalidatePath('/')
}

export async function deleteGallery(f: FormData) {
  await requireAdmin()
  const id = s(f, 'gallery_id')
  if (s(f, 'confirm') !== id) return        // ID 를 똑같이 입력해야만 삭제 (게시글·리포트가 모두 지워짐)
  await db()`delete from galleries where gallery_id = ${id}`
  revalidatePath('/admin/galleries')
}

export async function setFeedback(f: FormData) {
  await requireAdmin()
  const verdict = s(f, 'verdict')
  const id = Number(f.get('report_id'))
  const target = s(f, 'target')
  if (!Number.isInteger(id) || !/^(report|issue:\d|flood:\d)$/.test(target)) return
  if (verdict === 'clear') await db()`delete from report_feedback where report_id = ${id} and target = ${target}`
  else if (['ok', 'weak', 'wrong'].includes(verdict))
    await db()`insert into report_feedback (report_id, target, verdict) values (${id}, ${target}, ${verdict})
               on conflict (report_id, target) do update set verdict = excluded.verdict, created_at = now()`
  revalidatePath('/daily/[date]', 'page')
}

export async function saveTexts(f: FormData) {
  await requireAdmin()
  for (const d of TEXT_DEFS) {
    const raw = f.get(`ui.${d.key}`)
    if (raw == null) continue
    const v = String(raw).trim()
    if (!v || v === d.def) await db()`delete from settings where key = ${'ui.' + d.key}`           // 기본값이면 덮어쓰기를 지움
    else await db()`insert into settings (key, value) values (${'ui.' + d.key}, ${v})
                    on conflict (key) do update set value = excluded.value, updated_at = now()`
  }
  revalidatePath('/', 'layout')
}

export async function addRule(_p: Result, f: FormData): Promise<Result> {
  await requireAdmin()
  const pattern = s(f, 'pattern')
  if (!pattern || pattern.length > 300) return { ok: false, msg: '규칙(정규식)을 입력하세요.' }
  try { new RegExp(pattern) } catch { return { ok: false, msg: '정규식 형식이 올바르지 않습니다.' } }
  await db()`insert into noise_rules (pattern, note) values (${pattern}, ${s(f, 'note') || null}) on conflict do nothing`
  revalidatePath('/admin/rules')
  return { ok: true, msg: '추가했습니다. 다음 수집부터 새로 들어오는 글에 적용됩니다.' }
}

export async function ruleAction(f: FormData) {
  await requireAdmin()
  const id = Number(f.get('rule_id'))
  const act = s(f, 'act')
  if (act === 'delete') await db()`delete from noise_rules where id = ${id}`
  else if (act === 'toggle') await db()`update noise_rules set enabled = not enabled where id = ${id}`
  revalidatePath('/admin/rules')
}

export async function saveOverstatement(f: FormData) {
  await requireAdmin()
  const lines = s(f, 'map').split('\n').map(l => l.trim()).filter(Boolean)
  const map: Record<string, string> = {}
  for (const l of lines) {
    const [a, ...b] = l.split('=>')
    if (a?.trim() && b.length) map[a.trim()] = b.join('=>').trim()
  }
  await db()`insert into settings (key, value) values ('ai.overstatement_map', ${JSON.stringify(map)})
             on conflict (key) do update set value = excluded.value, updated_at = now()`
  revalidatePath('/admin/rules')
}

export async function saveSettings(f: FormData) {
  await requireAdmin()
  for (const d of SETTING_DEFS) {
    const v = s(f, d.key)
    if (v === '' || v === String(d.def)) await db()`delete from settings where key = ${d.key}`        // 기본값이면 덮어쓰기 제거
    else await db()`insert into settings (key, value) values (${d.key}, ${v}) on conflict (key) do update set value = excluded.value, updated_at = now()`
  }
  revalidatePath('/admin/settings')
}
