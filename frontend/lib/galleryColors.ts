const PALETTE: { bg: string; text: string }[] = [
  { bg: '#ede9fe', text: '#6d28d9' }, // violet
  { bg: '#ccfbf1', text: '#0f766e' }, // teal
  { bg: '#fce7f3', text: '#9d174d' }, // pink
  { bg: '#fef3c7', text: '#92400e' }, // amber
  { bg: '#e0e7ff', text: '#3730a3' }, // indigo
  { bg: '#cffafe', text: '#0e7490' }, // cyan
  { bg: '#ecfccb', text: '#3f6212' }, // lime
  { bg: '#ffe4e6', text: '#be123c' }, // rose
  { bg: '#e0f2fe', text: '#0369a1' }, // sky
  { bg: '#ffedd5', text: '#9a3412' }, // orange
  { bg: '#d1fae5', text: '#065f46' }, // emerald
  { bg: '#f3e8ff', text: '#6b21a8' }, // purple
]

function hashId(id: string): number {
  let h = 0
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0
  return h
}

export type GalleryColor = { bg: string; text: string }

export function galleryColor(galleryId: string): GalleryColor {
  return PALETTE[hashId(galleryId) % PALETTE.length]
}
