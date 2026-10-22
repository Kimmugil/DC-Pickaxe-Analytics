import { db } from '@/lib/db'

/** 갤러리 대표 이미지(DB에 저장된 JPEG). 하루 동안 브라우저·CDN에 캐시한다. */
export async function GET(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const [row] = await db()`select thumb from galleries where gallery_id = ${id}`
  if (!row?.thumb) return new Response('not found', { status: 404 })
  return new Response(new Uint8Array(row.thumb as Buffer), {
    headers: { 'Content-Type': 'image/jpeg', 'Cache-Control': 'public, max-age=3600, s-maxage=86400, stale-while-revalidate=604800' },
  })
}
