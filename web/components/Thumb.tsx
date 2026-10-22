const TINTS = ['bg-indigo-100 text-indigo-700', 'bg-emerald-100 text-emerald-700', 'bg-amber-100 text-amber-700', 'bg-rose-100 text-rose-700', 'bg-sky-100 text-sky-700', 'bg-violet-100 text-violet-700']

/** 갤러리 대표 이미지. 쓸 만한 이미지가 없으면 이름의 첫 글자로 만든 색 아바타를 보여준다. */
export function Thumb({ id, name, has = true, className = '' }: { id: string; name: string; has?: boolean; className?: string }) {
  if (has) {
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={`/api/thumb/${id}`} alt="" loading="lazy" className={`rounded-xl object-cover ring-1 ring-slate-200 ${className}`} />
  }
  const tint = TINTS[[...id].reduce((s, c) => s + c.charCodeAt(0), 0) % TINTS.length]
  return <div aria-hidden className={`grid place-items-center rounded-xl text-xl font-bold ${tint} ${className}`}>{[...name.trim()][0] ?? '?'}</div>
}
