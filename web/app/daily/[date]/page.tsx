import { redirect } from 'next/navigation'

/** 예전 주소: 날짜별 화면은 홈 캘린더의 '이 날 요약'으로 대체되었다 */
export default async function DailyDate({ params }: { params: Promise<{ date: string }> }) {
  const { date } = await params
  redirect(/^\d{4}-\d{2}-\d{2}$/.test(date) ? `/?month=${date.slice(0, 7)}&date=${date}` : '/')
}
