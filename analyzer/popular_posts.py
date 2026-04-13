"""
인기글 선정 모듈
- engagement score 기준으로 TOP N 선정

engagement_score = 추천수×2 + 댓글수×3 + 조회수×0.05
  (주간 분석 weekly_analyzer.py 와 동일한 공식 사용 — 일관성 유지)
"""
import pandas as pd
from typing import List


def get_top_posts(df: pd.DataFrame, n: int = 5) -> List[dict]:
    """
    engagement score 기준 상위 n개 게시글을 반환합니다.

    engagement_score = 추천수×2 + 댓글수×3 + 조회수×0.05

    Returns:
        [
            {
                글번호, 제목, 작성자, 날짜, 링크,
                댓글수, 조회수, 추천수, score
            },
            ...
        ]
    """
    if df.empty:
        return []

    df = df.copy()
    df['score'] = df['추천수'] * 2 + df['댓글수'] * 3 + df['조회수'] * 0.05
    top = df.nlargest(n, 'score')

    result = []
    for _, row in top.iterrows():
        result.append({
            '글번호': str(row.get('글번호', '')),
            '제목': str(row.get('제목', '')),
            '작성자': str(row.get('작성자', '')),
            '날짜': str(row.get('날짜', '')),
            '링크': str(row.get('링크', '')),
            '댓글수': int(row.get('댓글수', 0)),
            '조회수': int(row.get('조회수', 0)),
            '추천수': int(row.get('추천수', 0)),
            'score': int(row.get('score', 0)),
        })

    return result
