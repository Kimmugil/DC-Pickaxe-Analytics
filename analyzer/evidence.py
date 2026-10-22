"""유저 반응(긍정/부정)의 근거 검증. AI가 쓴 요약은 '입력으로 준 글번호·댓글 원문'으로 뒷받침될 때만 화면에 낸다.
- 인용한 댓글은 우리가 AI에게 준 댓글에 실제로 들어 있는지 코드가 확인한다 (지어낸 인용은 버린다).
- 근거(글 또는 댓글 인용)가 하나도 없는 반응은 아예 저장하지 않는다."""


def _norm(s: str) -> str:
    return "".join(str(s).split())


def verify_sentiment(raw, by_no: dict, comments: dict[int, list[str]]) -> dict:
    raw = raw if isinstance(raw, dict) else {}
    out = {}
    for side in ("positive", "negative"):
        v = raw.get(side)
        if isinstance(v, str):                                  # 예전 형식(문자열만)은 근거가 없으므로 버림
            continue
        if not isinstance(v, dict) or not str(v.get("summary", "")).strip():
            continue
        posts = [by_no[n] for n in dict.fromkeys(int(str(x).lstrip("#")) for x in (v.get("evidence") or []) if str(x).lstrip("#").isdigit()) if n in by_no]
        quotes = []
        for q in (v.get("quotes") or [])[:4]:
            if not isinstance(q, dict) or not str(q.get("post", "")).lstrip("#").isdigit():
                continue
            n, text = int(str(q["post"]).lstrip("#")), _norm(q.get("text", ""))
            if n not in by_no or len(text) < 8:
                continue
            orig = next((c for c in comments.get(n, []) if text[:24] in _norm(c) or _norm(c)[:24] in text), None)
            if orig:
                quotes.append({"text": orig, "title": by_no[n]["title"], "url": by_no[n]["url"]})
        if not posts and not quotes:
            continue
        out[side] = {"summary": str(v["summary"]).strip(),
                     "posts": [{"title": p["title"], "url": p["url"], "comment_count": p["comment_count"]} for p in posts[:3]],
                     "quotes": quotes[:3]}
    return out
