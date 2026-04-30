import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '디씨곡괭이 정련소',
  description: 'DC인사이드 키우기 장르 갤러리 동향 분석',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-50 text-gray-900">{children}</body>
    </html>
  )
}
