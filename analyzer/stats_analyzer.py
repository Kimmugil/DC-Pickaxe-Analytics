"""
게시글 통계 분석 모듈
- 일별/주별 게시글 수 추이
- 시간대별 분포, 작성자 분포
"""
import pandas as pd
from datetime import datetime, timedelta


def analyze_post_trends(df: pd.DataFrame, analysis_date: str = None) -> dict:
    """
    게시글 수 추이를 분석합니다.

    Returns:
        {
            daily_trend: [{date, count}, ...] (최근 30일),
            new_posts_today: int,
            new_posts_7d: int,
            total_posts: int,
        }
    """
    if df.empty:
        return {
            'daily_trend': [],
            'new_posts_today': 0,
            'new_posts_7d': 0,
            'total_posts': 0,
        }

    target = pd.to_datetime(analysis_date) if analysis_date else pd.Timestamp.now()
    month_ago = target - timedelta(days=30)
    week_ago = target - timedelta(days=7)

    df = df.copy()
    df_valid = df.dropna(subset=['날짜'])

    # 최근 30일 일별 추이
    recent = df_valid[df_valid['날짜'] >= month_ago].copy()
    recent['date_only'] = recent['날짜'].dt.date
    daily = (
        recent.groupby('date_only')
        .size()
        .reset_index(name='count')
    )
    daily['date_only'] = daily['date_only'].astype(str)

    today_count = len(df_valid[df_valid['날짜'].dt.date == target.date()])
    week_count = len(df_valid[df_valid['날짜'] >= week_ago])

    return {
        'daily_trend': daily.rename(columns={'date_only': 'date'}).to_dict('records'),
        'new_posts_today': today_count,
        'new_posts_7d': week_count,
        'total_posts': len(df),
    }


def analyze_activity(df: pd.DataFrame, analysis_date: str = None) -> dict:
    """
    활성도 지표를 분석합니다.

    Returns:
        {
            hourly_dist: {0~23: count},
            top_authors: {작성자: count},
            active_authors: int (7일 내 고유 작성자),
            peak_hour: int,
        }
    """
    if df.empty:
        return {
            'hourly_dist': {str(h): 0 for h in range(24)},
            'top_authors': {},
            'active_authors': 0,
            'peak_hour': 0,
        }

    target = pd.to_datetime(analysis_date) if analysis_date else pd.Timestamp.now()
    week_ago = target - timedelta(days=7)

    df_valid = df.dropna(subset=['날짜'])

    # 시간대별 분포 (0~23 모두 포함)
    hourly_counts = df_valid['날짜'].dt.hour.value_counts().to_dict()
    hourly_dist = {str(h): int(hourly_counts.get(h, 0)) for h in range(24)}

    # 작성자 분포
    author_counts = df['작성자'].value_counts()
    top_authors = {k: int(v) for k, v in author_counts.head(10).items()}

    # 7일 내 활성 작성자 수
    recent_authors = df_valid[df_valid['날짜'] >= week_ago]['작성자'].nunique()

    # 피크 시간대
    peak_hour = int(df_valid['날짜'].dt.hour.value_counts().idxmax()) if not df_valid.empty else 0

    return {
        'hourly_dist': hourly_dist,
        'top_authors': top_authors,
        'active_authors': int(recent_authors),
        'peak_hour': peak_hour,
    }
