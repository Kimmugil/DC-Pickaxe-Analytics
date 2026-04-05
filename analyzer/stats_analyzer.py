"""
게시글 통계 분석 모듈
- 일별/주별 게시글 수 추이
- 시간대별 분포

※ 작성자 집계(active_authors 등)는 제거됨.
  디씨인사이드는 닉네임 기반 수집으로 동일 닉네임(ㅇㅇ 등)이 다른 사람일 수 있어
  신뢰할 수 없는 데이터입니다.
"""
import pandas as pd
from datetime import datetime, timedelta


def analyze_post_trends(df: pd.DataFrame, analysis_date: str = None) -> dict:
    """
    게시글 수 추이를 분석합니다.

    analysis_date 기준:
    - new_posts_today: analysis_date 당일(00:00~23:59) 게시글 수
    - new_posts_7d: analysis_date 포함 최근 7일 게시글 수

    Returns:
        {
            daily_trend: [{date, count}, ...] (최근 30일),
            new_posts_today: int  (= analysis_date 24h 게시글 수),
            new_posts_7d: int,
            total_posts: int,
        }
    """
    if df.empty:
        return {'daily_trend': [], 'new_posts_today': 0, 'new_posts_7d': 0, 'total_posts': 0}

    target = pd.to_datetime(analysis_date) if analysis_date else pd.Timestamp.now() - pd.Timedelta(days=1)
    month_ago = target - timedelta(days=30)
    week_ago = target - timedelta(days=7)

    df_valid = df.dropna(subset=['날짜'])

    # 최근 30일 일별 추이
    recent = df_valid[df_valid['날짜'] >= month_ago].copy()
    recent['date_only'] = recent['날짜'].dt.date
    daily = recent.groupby('date_only').size().reset_index(name='count')
    daily['date_only'] = daily['date_only'].astype(str)

    # analysis_date 당일 게시글 수 (= 24h)
    day_count = len(df_valid[df_valid['날짜'].dt.date == target.date()])
    week_count = len(df_valid[df_valid['날짜'] >= week_ago])

    return {
        'daily_trend': daily.rename(columns={'date_only': 'date'}).to_dict('records'),
        'new_posts_today': day_count,
        'new_posts_7d': week_count,
        'total_posts': len(df),
    }


def analyze_activity(df: pd.DataFrame, analysis_date: str = None) -> dict:
    """
    시간대별 게시글 분포를 분석합니다.

    ※ active_authors(활성 작성자 수)는 신뢰도 문제로 제거됨.

    Returns:
        {
            hourly_dist: {"0"~"23": count},
            peak_hour: int,
        }
    """
    if df.empty:
        return {
            'hourly_dist': {str(h): 0 for h in range(24)},
            'peak_hour': 0,
        }

    df_valid = df.dropna(subset=['날짜'])

    hourly_counts = df_valid['날짜'].dt.hour.value_counts().to_dict()
    hourly_dist = {str(h): int(hourly_counts.get(h, 0)) for h in range(24)}
    peak_hour = int(df_valid['날짜'].dt.hour.value_counts().idxmax()) if not df_valid.empty else 0

    return {
        'hourly_dist': hourly_dist,
        'peak_hour': peak_hour,
    }
