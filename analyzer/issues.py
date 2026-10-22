"""AI가 만든 주제 목록의 후처리. AI가 정한 이름과 설명은 쓰되, '얼마나 큰 주제인지'는 AI가 아니라 코드가 실제 글로 잰다.

- AI는 주제마다 그 주제를 특정하는 키워드(keywords)와 근거 글번호(evidence)를 준다.
- 코드는 그날(또는 그 기간) 모든 글에서 키워드가 들어간 글을 세어 관련 글 수·댓글 합·비율을 계산한다.
- 주제는 AI의 나열 순서가 아니라 측정된 관심(댓글 합)으로 다시 정렬한다.
- 너무 작은 주제는 '소규모 화제'(근거 낮음)로 분류되어 화면에서 접힌다."""
from . import keywords as kw

# 게임 커뮤니티에서 어느 글에나 나올 수 있는 흔한 단어는 주제를 특정하지 못하므로 관련 글을 셀 때 쓰지 않는다
COMMON_GAME = {'이벤트', '업데이트', '패치', '공지', '운영', '게임', '유저', '캐릭터', '아이템', '콘텐츠', '컨텐츠', '보상', '이번', '오늘'}
STOP = kw.GENERIC | kw.PROFANITY | COMMON_GAME
TOO_COMMON = 0.35          # 전체 글의 35% 이상에 나오는 단어는 주제를 특정하지 못하므로 쓰지 않는다


def _hits(keywords, posts):
    """키워드가 제목(또는 가져온 본문)에 들어 있는 글. 너무 흔한 단어는 제외."""
    out = {}
    for k in dict.fromkeys(str(x).strip() for x in keywords):
        if len(k) < 2 or k in STOP:
            continue
        m = {p["post_no"]: p for p in posts if k in p["title"] or (p.get("body") and k in p["body"])}
        if m and len(m) <= TOO_COMMON * max(len(posts), 1):
            out.update(m)
    return out


def finalize_issues(issues, by_no: dict, all_posts, *, min_posts=5, min_share=0.02) -> list[dict]:
    total = max(len(all_posts), 1)
    total_comments = max(sum(p["comment_count"] for p in all_posts), 1)
    out = []
    for it in issues:
        ev = [n for n in dict.fromkeys(it.pop("evidence", [])) if n in by_no]     # 입력에 없는 글번호는 버림
        kws = [str(k) for k in (it.pop("keywords", None) or []) if str(k).strip()][:4]
        related = _hits(kws, all_posts)
        related.update({n: by_no[n] for n in ev})
        if not related:
            continue                                                        # 근거가 전혀 없는 주제는 만들지 않음
        keys = set(related)
        if any(keys and o["_keys"] and len(keys & o["_keys"]) / min(len(keys), len(o["_keys"])) >= 0.6 for o in out):
            continue                                                        # 관련 글이 거의 겹치면 같은 이야기로 보고 하나만 남김
        n_rel = len(related)
        csum = sum(p["comment_count"] for p in related.values())
        share, cshare = n_rel / total, csum / total_comments
        big = n_rel >= min_posts and (share >= min_share or cshare >= 3 * min_share)
        conf = "높음" if big and n_rel >= 15 else "보통" if big else "낮음"       # 낮음 = 소규모 화제
        top = sorted(related.values(), key=lambda p: (p["comment_count"], p["recommend_count"]), reverse=True)
        refs = [by_no[n] for n in ev][:3] or top[:3]
        it.update({"ref_posts": [{"title": p["title"], "url": p["url"], "comment_count": p["comment_count"]} for p in refs],
                   "mention_count": n_rel, "comment_sum": csum, "share_posts": round(share * 100, 1), "share_comments": round(cshare * 100, 1),
                   "keywords": kws, "confidence": conf, "evidence_nos": ev, "_keys": keys})
        out.append(it)
    out.sort(key=lambda it: (it["comment_sum"], it["mention_count"]), reverse=True)      # 관심 순위는 측정값으로
    for it in out:
        it.pop("_keys", None)
    return out
