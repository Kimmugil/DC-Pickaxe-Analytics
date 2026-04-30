"""
한국어 키워드 추출

kiwipiepy가 설치된 환경에서는 형태소 분석기(명사 추출)를 사용하고,
없을 경우 정규식 기반으로 폴백합니다.
제목(제목)과 본문(본문) 상위 100자를 모두 활용합니다.
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

_MIN_LEN   = 2
_kiwi      = None
_kiwi_tried = False


def _get_kiwi():
    global _kiwi, _kiwi_tried
    if not _kiwi_tried:
        _kiwi_tried = True
        try:
            from kiwipiepy import Kiwi
            _kiwi = Kiwi()
        except Exception:
            _kiwi = None
    return _kiwi


def _extract_with_kiwi(text: str) -> list[str]:
    kiwi = _get_kiwi()
    if kiwi is None:
        return []
    try:
        tokens = kiwi.tokenize(text)
        return [
            t.form for t in tokens
            if t.tag.startswith("NN")   # 명사류(NNG, NNP, NNB 등)
            and len(t.form) >= _MIN_LEN
            and t.form not in _STOPWORDS
        ]
    except Exception:
        return []


def _extract_with_regex(text: str) -> list[str]:
    tokens = re.findall(r"[가-힣a-zA-Z]{2,}", text)
    return [
        t for t in tokens
        if len(t) >= _MIN_LEN
        and t not in _STOPWORDS
        and not re.fullmatch(r"[0-9]+", t)
    ]


def extract(posts: list[dict], top_n: int = 15) -> list[list]:
    """
    게시글 제목 + 본문(상위 100자)에서 상위 키워드를 추출합니다.

    Args:
        posts: 게시글 dict 리스트 (제목, 본문 키 사용)
        top_n: 반환할 키워드 수

    Returns:
        [[keyword, count], ...] 빈도 내림차순
    """
    if not posts:
        return []

    texts = []
    for p in posts:
        title = str(p.get("제목", "") or "")
        body  = str(p.get("본문",  "") or "")[:100]
        texts.append(title + " " + body)
    combined = " ".join(texts)

    words = _extract_with_kiwi(combined) or _extract_with_regex(combined)
    counter = Counter(words)
    return [[kw, cnt] for kw, cnt in counter.most_common(top_n)]
