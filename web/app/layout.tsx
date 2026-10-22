import type { Metadata } from 'next'
import './globals.css'
import { Nav } from '@/components/Nav'
import { getTexts, T } from '@/lib/texts'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: '디씨곡괭이 정련소',
  description: 'DC인사이드 갤러리 동향 분석',
}

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const t = await getTexts()
  return (
    <html lang="ko">
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <Nav />
        <main className="max-w-6xl mx-auto px-4 py-8">{children}</main>
        <footer className="max-w-6xl mx-auto px-4 pb-12 text-xs text-slate-400">{T(t, 'footer.disclaimer')}</footer>
      </body>
    </html>
  )
}
