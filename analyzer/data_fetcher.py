"""
분석 대상 게시글 선정 모듈

선정 기준 [3]:
- 1순위: analysis_date 당일(00:00~23:59) 게시글 전체
- 2순위: 최근 7일 내 인기글 최대 15개 (24h 게시글에 없는 것, 맥락 참고용)
- engagement_score 내림차순 정렬 → AI가 중요한 게시글을 먼저 읽음
- MAX_POSTS_FOR_AI 초과 시 상위 게시글만 유지
"""
import pandas as pd
from datetime import timedelta

MAX_POSTS_FOR_AI = 80   # AI에 전달할 최대 게시글 수
CONTEXT_POSTS    = 15   # 7일 내 인기글 참고용 최대 수


def select_posts_for_analysis(
    df: pd.DataFrame,
    analysis_date: str = None,
    max_posts: int = MAX_POSTS_FOR_AI,
) -> pd.DataFrame:
    """
    분석 대상 게시글을 선정합니다.

    Args:
        df: 갤러리 게시글 전체 DataFrame
        analysis_date: 분석 기준일 (None이면 어제)
        max_posts: AI에 전달할 최대 게시글 수

    Returns:
        '선택이유', 'engagement_score' 컬럼이 추가된 DataFrame
        (engagement_score 내림차순 정렬)
    """
    if df.empty:
        return df

    target = (
        pd.to_datetime(analysis_date)
        if analysis_date
        else pd.Timestamp.now() - pd.Timedelta(days=1)
    )
    week_ago = target - timedelta(days=7)

    df = df.copy()
    df['engagement_score'] = df['추천수'] * 2 + df['댓글수'] + df['조회수'] * 0.1

    # 1순위: 분석 기준일 당일 게시글 전체
    day_mask = df['날짜'].dt.date == target.date()
    day_df = df[day_mask].copy()
    day_df['선택이유'] = '분석기준일(24h)'

    # 2순위: 최근 7일 내 인기글 (당일 게시글 제외, 맥락 참고용)
    week_mask = (df['날짜'] >= week_ago) & (~day_mask)
    ctx_df = df[week_mask].nlargest(CONTEXT_POSTS, 'engagement_score').copy()
    ctx_df['선택이유'] = '최근7일인기글(참고)'

    combined = (
        pd.concat([day_df, ctx_df])
        .drop_duplicates(subset=['글번호'])
        .sort_values('engagement_score', ascending=False)
    )

    if len(combined) > max_posts:
        combined = combined.head(max_posts)

    return combined.reset_index(drop=True)
