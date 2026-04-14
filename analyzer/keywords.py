"""
한국어 키워드 추출 — kiwipiepy 기반

게시글 제목 + 본문에서 명사류 키워드를 추출하고 빈도 집계.
불용어, 단순 조사/어미, 짧은 단어 제거.
"""

from __future__ import annotations
import re
from collections import Counter

# ── 불용어 목록 ───────────────────────────────────────────────────────
_STOPWORDS = {
    # 일반 불용어
    "이거", "저거", "그거", "이건", "저건", "그건", "이게", "저게", "그게",
    "것", "수", "때", "곳", "중", "등", "분", "명", "번", "개",
    "이제", "그냥", "진짜", "정말", "너무", "매우", "아주", "거의", "이미",
    "다시", "또", "더", "좀", "막", "다", "좀", "왜", "어",
    "ㅋㅋ", "ㅋㅋㅋ", "ㅠㅠ", "ㅎㅎ", "ㅜㅜ",
    # 게임 갤러리 공통 불용어
    "갤러리", "갤", "게임", "유저", "사람", "생각", "질문", "댓글",
    "글", "글쓴이", "작성자", "ㅇㅇ", "ㄷㄷ",
    # DC 관련
    "dcinside", "gall", "board", "view", "mgallery",
}

_MIN_LEN = 2       # 최소 글자 수
_TOP_N   = 15      # 반환 키워드 수


def extract(posts: list[dict], top_n: int = _TOP_N) -> list[list]:
    """
    게시글 목록에서 상위 키워드를 추출합니다.

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
        body  = str(p.get("본문",  "") or "")
        texts.append(title + " " + body)
    combined = " ".join(texts)

    try:
        return _extract_kiwi(combined, top_n)
    except Exception:
        return _extract_simple(combined, top_n)


def _extract_kiwi(text: str, top_n: int) -> list[list]:
    from kiwipiepy import Kiwi
    kiwi   = Kiwi()
    tokens = kiwi.tokenize(text)
    words  = []
    for tok in tokens:
        if tok.tag not in ("NNG", "NNP", "SL"):   # 일반명사, 고유명사, 외래어
            continue
        w = tok.form.strip()
        if len(w) < _MIN_LEN:
            continue
        if w in _STOPWORDS:
            continue
        if re.fullmatch(r"[0-9]+", w):            # 순수 숫자 제외
            continue
        words.append(w)
    counter = Counter(words)
    return [[kw, cnt] for kw, cnt in counter.most_common(top_n)]


def _extract_simple(text: str, top_n: int) -> list[list]:
    """kiwipiepy 사용 불가 시 단순 토큰 분리 fallback."""
    tokens = re.findall(r"[가-힣a-zA-Z]{2,}", text)
    words  = [t for t in tokens if t not in _STOPWORDS and len(t) >= _MIN_LEN]
    counter = Counter(words)
    return [[kw, cnt] for kw, cnt in counter.most_common(top_n)]
