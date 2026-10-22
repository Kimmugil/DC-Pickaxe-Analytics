import { galleries } from '@/lib/queries'
import { AddGalleryForm } from '@/components/AdminForms'
import { Card, Chip, PageHeader } from '@/components/kit'
import { addGallery, deleteGallery, updateGallery } from '../actions'

export const dynamic = 'force-dynamic'

const TYPE = { major: '일반', minor: '마이너', mini: '미니' } as Record<string, string>

export default async function GalleriesAdmin() {
  const gals = await galleries()
  return (
    <div>
      <PageHeader title="갤러리" sub={`추적 ${gals.filter(g => g.is_active).length}곳 · 중단 ${gals.filter(g => !g.is_active).length}곳`} />
      <div className="mb-6"><AddGalleryForm action={addGallery} /></div>

      <Card className="divide-y divide-slate-100">
        {gals.map(g => (
          <details key={g.gallery_id} className="group">
            <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1 px-4 py-3 hover:bg-slate-50">
              <span className="text-slate-300 transition-transform group-open:rotate-90">›</span>
              <span className="font-semibold">{g.name}</span>
              <span className="text-xs text-slate-400">/{g.gallery_id} · {TYPE[g.gallery_type]} · {g.collect_interval_min}분마다</span>
              <Chip tone={g.is_active ? 'green' : 'gray'}>{g.is_active ? '수집 중' : '수집 꺼짐'}</Chip>
              <span className="ml-auto text-xs text-slate-400">마지막 수집 {g.last_collected ?? '-'}{g.last_result ? ` · ${g.last_result}` : ''}</span>
            </summary>
            <div className="space-y-4 border-t border-slate-100 bg-slate-50/50 px-5 py-4">
              <form action={updateGallery} className="space-y-4">
                <input type="hidden" name="gallery_id" value={g.gallery_id} />
                <div className="grid gap-3 sm:grid-cols-5">
                  <div><label className="label">표시 이름</label><input name="name" defaultValue={g.name} className="input" /></div>
                  <div><label className="label">캘린더 약칭 (짧게)</label><input name="short_name" defaultValue={g.short_name ?? ''} maxLength={10} className="input" placeholder="예: 메이플" /></div>
                  <div><label className="label">수집 주기(분)</label><input name="collect_interval_min" type="number" min={15} max={1440} defaultValue={g.collect_interval_min} className="input" /></div>
                  <div><label className="label">이슈 기준 가감 (-2~+3)</label><input name="issue_threshold_adjust" type="number" min={-2} max={3} defaultValue={g.issue_threshold_adjust} className="input" /></div>
                  <div><label className="label">이슈 최소 게시량</label><input name="min_issue_posts" type="number" min={0} defaultValue={g.min_issue_posts} className="input" /></div>
                </div>
                <div>
                  <label className="label">용어사전 (AI 참고용 · 한 줄에 하나, <code>단어: 설명</code>)</label>
                  <textarea name="notes" rows={4} defaultValue={g.notes ?? ''} className="input font-mono" placeholder={'이환: 갤러리에서 자주 언급되는 인물 별명\n메키: 메이플 키우기 줄임말'} />
                </div>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="is_active" defaultChecked={g.is_active} /> 수집 켜기</label>
                  <button className="btn">저장</button>
                </div>
              </form>
              <form action={deleteGallery} className="flex flex-wrap items-center gap-2 border-t border-slate-200 pt-3 text-sm">
                <input type="hidden" name="gallery_id" value={g.gallery_id} />
                <span className="text-rose-600">삭제 (글·리포트가 모두 사라지며 복구할 수 없습니다):</span>
                <input name="confirm" className="input !w-52" placeholder={`확인용으로 ${g.gallery_id} 입력`} />
                <button className="btn-danger">삭제</button>
              </form>
            </div>
          </details>
        ))}
      </Card>
      <p className="mt-3 text-xs text-slate-500">되도록 삭제 대신 &quot;수집 끄기&quot;를 쓰세요. 끄면 새 글은 가져오지 않지만 지금까지의 기록은 화면에 남습니다.</p>
    </div>
  )
}
