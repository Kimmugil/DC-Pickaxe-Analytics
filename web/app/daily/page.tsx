import { redirect } from 'next/navigation'

/** 예전 주소: 일별 캘린더는 이제 홈에 있다 */
export default async function Daily({ searchParams }: { searchParams: Promise<{ month?: string }> }) {
  const sp = await searchParams
  redirect(sp.month ? `/?month=${sp.month}` : '/')
}
