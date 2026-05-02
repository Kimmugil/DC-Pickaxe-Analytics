export interface TopPost {
  제목: string
  링크: string
  날짜?: string
  댓글수: number
  추천수: number
  조회수: number
  score?: number
}

export interface DailyIssue {
  date: string
  run_id?: string
  gallery_id: string
  gallery_name: string
  posts_total: number
  avg_7d: number
  avg_same_weekday?: number
  momentum_avg?: number
  issue_score: number
  has_issue: boolean
  is_borderline?: boolean
  keywords: [string, number][] | null
  top_posts: TopPost[] | null
  ai_summary: string
  temperature_tag?: string
  issue_cause?: string
  recent_issue_days?: number
}

export interface WeeklyGallery {
  week_start: string
  week_end: string
  run_id?: string
  gallery_id: string
  gallery_name: string
  total_posts: number
  daily_counts: Record<string, number> | null
  keywords: [string, number][] | null
  top_posts: TopPost[] | null
  ai_summary: string
}

export interface WeeklyData {
  galleries: WeeklyGallery[]
  overall: {
    week_start?: string
    week_end?: string
    ai_summary?: string
  }
}
