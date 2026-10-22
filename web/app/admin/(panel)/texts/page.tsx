import { getTexts } from '@/lib/texts'
import { TEXT_DEFS } from '@/lib/textDefs'
import { TextsEditor } from '@/components/TextsEditor'
import { PageHeader } from '@/components/kit'
import { saveTexts } from '../actions'

export const dynamic = 'force-dynamic'

export default async function TextsAdmin() {
  const t = await getTexts()
  return (
    <div>
      <PageHeader title="화면 문구" sub="사이트에 보이는 제목·안내문을 직접 고칩니다. 저장하면 바로 반영됩니다. {count} 같은 부분은 숫자가 들어가는 자리이니 그대로 두세요" />
      <TextsEditor rows={TEXT_DEFS.map(d => ({ ...d, value: t[d.key] ?? d.def }))} action={saveTexts} />
    </div>
  )
}
