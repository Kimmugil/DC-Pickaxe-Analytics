"""
주간 분석 모듈
- 갤러리별 주간 통계 (총 게시글, 일별 추이, TOP5, 키워드)
- 정규화 추이 데이터 (각 갤러리 max=100)
"""
import pandas as pd
from datetime import date, timedelta
from typing import Optional


def _score_post(post: dict) -> float:
    return post.get('추천수', 0) * 2 + post.get('댓글수', 0) * 3 + post.get('조회수', 0) * 0.05


def analyze_gallery_weekly(
    gallery: dict,
    week_start: date,
    week_end: date,
) -> Optional[dict]:
    """
    갤러리 한 개의 주간(월~일) 통계를 분석합니다.

    Returns:
        {
            gallery_id, gallery_name,
            total_posts_week,
            daily_counts: {'YYYY-MM-DD': count, ...},
            top5_posts: [...],
            top_keywords: [(keyword, count), ...],
        }
        or None if no data
    """
    from sheets.reader import get_gallery_posts
    from analyzer.keyword_analyzer import extract_keywords

    gallery_name = gallery.get('갤러리명') or gallery.get('gallery_name', '?')
    gallery_id   = gallery.get('갤러리ID') or gallery.get('gallery_id', '')
    sheet_url    = (gallery.get('저장시트 URL') or gallery.get('저장시트URL')
                    or gallery.get('sheet_url', ''))

    if not sheet_url:
        return None

    df = get_gallery_posts(sheet_url)
    if df.empty:
        return None

    # 날짜 범위 필터
    ts_start = pd.Timestamp(week_start)
    ts_end   = pd.Timestamp(week_end) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    week_df  = df[(df['날짜'] >= ts_start) & (df['날짜'] <= ts_end)].copy()

    if week_df.empty:
        return {
            'gallery_id': gallery_id, 'gallery_name': gallery_name,
            'total_posts_week': 0, 'daily_counts': {},
            'top5_posts': [], 'top_keywords': [],
        }

    # 일별 게시글 수
    daily_counts: dict[str, int] = {}
    current = week_start
    while current <= week_end:
        day_str = current.strftime('%Y-%m-%d')
        count   = int((week_df['날짜'].dt.date == current).sum())
        daily_counts[day_str] = count
        current += timedelta(days=1)

    # TOP5 (engagement score 기준)
    week_df['_score'] = (week_df['추천수'] * 2
                         + week_df['댓글수'] * 3
                         + week_df['조회수'] * 0.05)
    top5_df = week_df.nlargest(5, '_score')
    top5 = []
    for _, row in top5_df.iterrows():
        top5.append({
            '제목':   str(row.get('제목', '')),
            '링크':   str(row.get('링크', '')),
            '댓글수': int(row.get('댓글수', 0)),
            '조회수': int(row.get('조회수', 0)),
            '추천수': int(row.get('추천수', 0)),
            '날짜':   str(row.get('날짜', ''))[:10],
            'score':  round(float(row.get('_score', 0)), 1),
        })

    # 키워드 (최대 5개)
    keywords = extract_keywords(week_df)[:5]

    return {
        'gallery_id':       gallery_id,
        'gallery_name':     gallery_name,
        'total_posts_week': len(week_df),
        'daily_counts':     daily_counts,
        'top5_posts':       top5,
        'top_keywords':     keywords,
    }


def normalize_trends(gallery_results: list[dict]) -> list[dict]:
    """
    각 갤러리의 일별 게시글 수를 해당 갤러리의 최대치=100 기준으로 정규화합니다.
    갤러리 간 절대 수치 차이를 무시하고 상대적 추이를 볼 수 있게 합니다.

    Returns:
        [{'name': str, 'items': [(date_str, normalized_count), ...], 'color': str}, ...]
    """
    from dashboard.dash_styles import gallery_color

    series = []
    for idx, result in enumerate(gallery_results):
        counts_map = result.get('daily_counts', {})
        if isinstance(counts_map, str):
            import json
            try:
                counts_map = json.loads(counts_map)
            except Exception:
                counts_map = {}

        if not counts_map:
            continue

        sorted_items = sorted(counts_map.items())
        values = [v for _, v in sorted_items]
        max_v  = max(values) if values else 1
        if max_v == 0:
            max_v = 1

        normalized = [(d, round(v / max_v * 100, 1)) for d, v in sorted_items]
        series.append({
            'name':  result.get('gallery_name', ''),
            'items': normalized,
            'color': gallery_color(idx),
        })

    return series
