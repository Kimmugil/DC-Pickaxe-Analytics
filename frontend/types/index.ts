export interface TopPost {
  제목: string
  링크: string
  날짜?: string
  댓글수: number
  추천수: number
  조회수: number
  score?: number
}

export interface CategoryScore {
  score: number      // 0~3
  summary: string
}

export interface MajorIssue {
  title: string
  detail: string
  mention_count: number
  ref_url: string
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
  // v2 structured fields
  headline?: string
  temperature_tag?: string
  issue_cause?: string
  category_scores?: {
    balance:   CategoryScore
    operation: CategoryScore
    bug:       CategoryScore
    payment:   CategoryScore
    content:   CategoryScore
  }
  major_issues?: MajorIssue[]
  sentiment?: {
    positive: string
    negative: string
  }
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
  // v2 structured fields
  headline?: string
  temperature_tag?: string
  top_cause?: string
  category_scores?: {
    balance:   CategoryScore
    operation: CategoryScore
    bug:       CategoryScore
    payment:   CategoryScore
    content:   CategoryScore
  }
  major_issues?: Omit<MajorIssue, 'ref_url'>[]
  sentiment?: {
    positive: string
    negative: string
  }
}

export interface WeeklyData {
  galleries: WeeklyGallery[]
  overall: {
    week_start?: string
    week_end?: string
    ai_summary?: string
  }
}

export interface MonthlyGallery {
  month: string
  run_id?: string
  gallery_id: string
  gallery_name: string
  issue_days: number
  total_issue_score: number
  max_issue_score: number
  top_cause: string
  keywords: [string, number][] | null
  headlines: string[] | null
  ai_summary: string
  // v2 structured fields
  headline?: string
  temperature_tag?: string
  category_scores?: {
    balance:   CategoryScore
    operation: CategoryScore
    bug:       CategoryScore
    payment:   CategoryScore
    content:   CategoryScore
  }
  major_issues?: Omit<MajorIssue, 'ref_url'>[]
  sentiment?: {
    positive: string
    negative: string
  }
}

export interface MonthlyOverall {
  month: string
  run_id?: string
  ai_summary: string
}
