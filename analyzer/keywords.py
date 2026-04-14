"""
한국어 키워드 추출 — 정규식 기반

게시글 제목에서 명사성 단어를 추출하고 빈도 집계.
kiwipiepy 의존성 없이 동작 (네트워크/설치 환경 무관).
"""

from __future__ import annotations
import re
from collections import Counter

_STOPWORDS = {
    "이거", "저거", "그거", "이건", "저건", "그건", "이게", "저게", "그게",
    "것", "수", "때", "곳", "중", "등", "분", "명", "번", "개",
    "이제", "그냥", "진짜", "정말", "너무", "매우", "아주", "거의", "이미",
    "다시", "또", "더", "좀", "막", "다", "왜", "어",
    "갤러리", "갤", "게임", "유저", "사람", "생각", "질문", "댓글",
    "글", "글쓴이", "작성자",
    "dcinside", "gall", "board", "view", "mgallery",
    "ㅋㅋ", "ㅋㅋㅋ", "ㅠㅠ", "ㅎㅎ", "ㅜㅜ", "ㅇㅇ", "ㄷㄷ",
}

_MIN_LEN = 2


def extract(posts: list[dict], top_n: int = 15) -> list[list]:
    """
    게시글 제목에서 상위 키워드를 추출합니다.

    Args:
        posts: 게시글 dict 리스트 (제목 키 사용)
        top_n: 반환할 키워드 수

    Returns:
        [[keyword, count], ...] 빈도 내림차순
    """
    if not posts:
        return []

    combined = " ".join(str(p.get("제목", "") or "") for p in posts)
    tokens = re.findall(r"[가-힣a-zA-Z]{2,}", combined)
    words = [
        t for t in tokens
        if len(t) >= _MIN_LEN
        and t not in _STOPWORDS
        and not re.fullmatch(r"[0-9]+", t)
    ]
    counter = Counter(words)
    return [[kw, cnt] for kw, cnt in counter.most_common(top_n)]
