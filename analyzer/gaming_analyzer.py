"""
키우기 게임 특화 분석 모듈
- 패치/업데이트 반응, 과금 민심, 버그 리포트, 컨텐츠 소진 신호 등을 감지
"""
import re
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict

# ─── 신호별 키워드 패턴 ────────────────────────────────────────────
SIGNAL_PATTERNS: Dict[str, list] = {
    'patch_buzz':             ['업데이트', '패치', '공지', '점검', '업뎃', '신규'],
    'guide_ratio':            ['공략', '팁', '추천', '방법', '알려', '어떻게', '초보', '뉴비'],
    'content_exhaustion':     ['할거없', '지루', '접겠', '탈주', '질렸', '재미없', '노잼', '망겜', '접자'],
    'monetization_sentiment': ['과금', '가챠', '확률', '환불', '유료', '현질', '뽑기', '패스'],
    'bug_reports':            ['버그', '오류', '튕김', '신고', '오작동', '에러', '먹통', '렉'],
    'event_buzz':             ['이벤트', '기간한정', '콜라보', '콜라', '이벤'],
    'balance_complaints':     ['밸런스', '너프', '버프', '사기캐', '약캐', '불균형'],
    'newcomer_signal':        ['시작했', '처음', '입문', '뉴비', '초보', '시작하는'],
    'endgame_signal':         ['만렙', '엔드', '클리어', '올클', '다깼', '컨텐츠 없'],
}

SIGNAL_LABELS = {
    'patch_buzz':             '패치/업데이트 반응',
    'guide_ratio':            '공략/팁 수요 (신규유입 지표)',
    'content_exhaustion':     '컨텐츠 소진 징후',
    'monetization_sentiment': '과금/확률 민심',
    'bug_reports':            '버그/오류 리포트',
    'event_buzz':             '이벤트 화제성',
    'balance_complaints':     '밸런스 불만',
    'newcomer_signal':        '신규 유저 유입 신호',
    'endgame_signal':         '엔드게임 진입 신호',
}


def analyze_gaming_signals(df: pd.DataFrame) -> Dict:
    """
    키우기 게임 특화 신호를 분석합니다.

    Returns:
        {
            signal_name: {
                label: str,
                keyword_hits: int,       # 전체 키워드 등장 횟수
                post_count: int,         # 해당 신호 관련 게시글 수
                ratio: float,            # 전체 대비 비율(%)
            },
            retention_signal: {          # 재방문 작성자 지표
                repeat_authors_7d: int,
                ratio: float,
            }
        }
    """
    if df.empty:
        return {}

    total = len(df)
    titles_combined = ' '.join(df['제목'].fillna('').tolist())
    bodies_combined = ' '.join(df['본문'].fillna('').tolist())
    all_text = (titles_combined + ' ' + bodies_combined).lower()

    signals = {}
    for signal_name, keywords in SIGNAL_PATTERNS.items():
        keyword_hits = sum(all_text.count(kw) for kw in keywords)
        matching = df[
            df['제목'].str.contains('|'.join(re.escape(kw) for kw in keywords), na=False, case=False)
        ]
        signals[signal_name] = {
            'label': SIGNAL_LABELS.get(signal_name, signal_name),
            'keyword_hits': keyword_hits,
            'post_count': len(matching),
            'ratio': round(len(matching) / total * 100, 1) if total > 0 else 0.0,
        }

    # 재방문 작성자 지표 (7일 내 2회 이상 작성)
    df_valid = df.dropna(subset=['날짜']) if '날짜' in df.columns else df
    if not df_valid.empty:
        week_ago = datetime.now() - timedelta(days=7)
        recent = df_valid[df_valid['날짜'] >= week_ago] if '날짜' in df_valid.columns else df_valid
        if not recent.empty:
            author_freq = recent['작성자'].value_counts()
            repeat_count = int((author_freq >= 2).sum())
            total_authors = int(author_freq.nunique())
            signals['retention_signal'] = {
                'label': '재방문 작성자 비율 (리텐션 지표)',
                'repeat_authors_7d': repeat_count,
                'ratio': round(repeat_count / total_authors * 100, 1) if total_authors > 0 else 0.0,
            }

    return signals
