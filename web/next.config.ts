import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  poweredByHeader: false,
  // 예전 주소(주간·월간·일별 목록)는 갤러리 페이지로 통합되었다
  async redirects() {
    return [
      { source: '/weekly/:path*', destination: '/gallery', permanent: false },
      { source: '/monthly/:path*', destination: '/gallery', permanent: false },
    ]
  },
}

export default nextConfig
