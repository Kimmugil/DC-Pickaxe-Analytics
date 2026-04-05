"""
분석 대상 게시글 선정 모듈
- 최근 7일 내 게시글 + 전체 인기글 조합으로 분석 대상 선정
- 선정된 게시글은 run_id와 함께 '분석대상게시글' 시트에 기록됨
"""
import pandas as pd
from datetime import datetime, timedelta


def select_posts_for_analysis(
    df: pd.DataFrame,
    analysis_date: str = None,
    max_posts: int = 50,
) -> pd.DataFrame:
    """
    분석 대상 게시글을 선정합니다.

    선정 기준:
    1. 최근 7일 이내 게시글 (전수 포함, 단 max_posts 초과 시 engagement 순 정렬)
    2. 7일 이전 인기글 최대 10개 (오래됐지만 반응이 컸던 글)
    3. 전체 max_posts 개수 제한

    Args:
        df: 갤러리 게시글 전체 DataFrame
        analysis_date: 기준 날짜 문자열 (None이면 오늘)
        max_posts: 최대 선정 게시글 수

    Returns:
        '선택이유' 컬럼이 추가된 DataFrame
    """
    if df.empty:
        return df

    target_date = pd.to_datetime(analysis_date) if analysis_date else pd.Timestamp.now()
    week_ago = target_date - timedelta(days=7)

    df = df.copy()
    df['engagement_score'] = df['추천수'] * 2 + df['댓글수']

    # 최근 7일 게시글
    recent_mask = df['날짜'] >= week_ago
    recent_df = df[recent_mask].copy()
    recent_df['선택이유'] = '최근7일'

    # 7일 이전 인기글 (최대 10개)
    old_popular_df = df[~recent_mask].nlargest(10, 'engagement_score').copy()
    old_popular_df['선택이유'] = '과거인기글'

    combined = pd.concat([recent_df, old_popular_df]).drop_duplicates(subset=['글번호'])

    # max_posts 초과 시 engagement 순으로 자름
    if len(combined) > max_posts:
        combined = combined.nlargest(max_posts, 'engagement_score')

    return combined.reset_index(drop=True)
