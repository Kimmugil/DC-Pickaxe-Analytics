"""주제 키워드 추출.
- 형태소 분석기(kiwipiepy)가 있으면 명사를, 없으면 정규식으로 단어를 뽑는다.
- 욕설·일반어는 '주제 키워드'에서만 뺀다(원본 글은 그대로, 욕설 횟수는 따로 센다).
- '평소보다 튄 단어'(rising)는 최근 28일 일평균(keyword_daily)과 비교해 구한다."""
import re
from collections import Counter

GENERIC = {
    "이거", "저거", "그거", "이건", "저건", "그건", "이게", "저게", "그게", "것", "수", "때", "곳", "중", "등", "분", "명", "번", "개",
    "이제", "그냥", "진짜", "정말", "너무", "매우", "아주", "거의", "이미", "다시", "또", "더", "좀", "막", "다", "왜", "어",
    "갤러리", "게임", "유저", "사람", "생각", "질문", "댓글", "글", "글쓴이", "작성자", "정도", "처음", "계속", "지금", "오늘", "내일",
    "근데", "이번", "하나", "그래", "얘기", "이상", "때문", "하면", "해서", "그리고", "사실", "아직", "나중", "이유",
    "ㅋㅋ", "ㅋㅋㅋ", "ㅠㅠ", "ㅎㅎ", "ㅜㅜ", "ㅇㅇ", "ㄷㄷ", "dcinside", "gall", "board", "view", "mgallery",
}
PROFANITY = {"새끼", "시발", "씨발", "병신", "지랄", "좆", "개새끼", "새기", "븅신", "미친", "존나", "ㅅㅂ", "ㅂㅅ", "ㅈㄴ", "염병", "시팔"}

_kiwi, _kiwi_tried = None, False


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


def tokens(text: str) -> list[str]:
    kiwi = _get_kiwi()
    if kiwi is not None:
        try:
            return [t.form for t in kiwi.tokenize(text) if t.tag.startswith("NN") and len(t.form) >= 2]
        except Exception:
            pass
    return [t for t in re.findall(r"[가-힣a-zA-Z]{2,}", text)]


def extract(posts, top_n=10):
    """posts → (주제 키워드 [[단어, 글 수]...], 욕설 글 비율 정보)
    같은 글 안에서 반복된 단어는 한 번만 센다(= 몇 개 글에서 언급됐는지)."""
    topic, prof_posts = Counter(), 0
    for p in posts:
        words = set(tokens(p["title"] + " " + (p.get("body") or "")[:100]))
        if words & PROFANITY:
            prof_posts += 1
        for w in words:
            if w not in GENERIC and w not in PROFANITY and not w.isdigit():
                topic[w] += 1
    return topic, prof_posts


def rising(conn, gid, day, topic: Counter, top_n=5, min_count=5, factor=3.0):
    """오늘 언급 글 수가 최근 28일 일평균의 factor배 이상인 단어."""
    rows = conn.execute(
        """select keyword, sum(count)::float s from keyword_daily
           where gallery_id = %s and day >= %s::date - 28 and day < %s group by keyword""", (gid, day, day)).fetchall()
    n_days = conn.execute(
        "select count(distinct day) n from keyword_daily where gallery_id = %s and day >= %s::date - 28 and day < %s",
        (gid, day, day)).fetchone()["n"]
    if n_days < 5:
        return []
    mean = {r["keyword"]: r["s"] / n_days for r in rows}
    out = [(w, c, min(10.0, round(c / max(mean.get(w, 0.0), 1.0), 1))) for w, c in topic.items()   # 10배 이상은 '10'으로 묶음(평소 거의 없던 단어의 과장 방지)
           if c >= min_count and c >= factor * max(mean.get(w, 0.0), 1.0)]
    out.sort(key=lambda x: (x[2], x[1]), reverse=True)
    return [[w, c, ratio] for w, c, ratio in out[:top_n]]


def save_daily(conn, gid, day, topic: Counter, keep=60):
    rows = [(gid, day, w, c) for w, c in topic.most_common(keep)]
    if rows:
        with conn.cursor() as cur:
            cur.executemany(
                "insert into keyword_daily (gallery_id, day, keyword, count) values (%s,%s,%s,%s) "
                "on conflict (gallery_id, day, keyword) do update set count = excluded.count", rows)


def register_terms(terms):
    """관리자가 용어사전에 적은 단어를 형태소 분석기에 고유명사로 등록(예: 슬랭·닉네임이 쪼개지는 것을 방지)."""
    kiwi = _get_kiwi()
    if kiwi is None:
        return
    for t in terms:
        t = t.strip()
        if len(t) >= 2:
            try:
                kiwi.add_user_word(t, "NNP")
            except Exception:
                pass
