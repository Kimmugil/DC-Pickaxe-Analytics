"""도배(같은 제목의 반복) 묶음 감지.

작성자(닉네임·IP)는 보지 않는다: 기본 닉네임을 여러 사람이 공유하고 IP로는 동일인을 알 수 없기 때문.
'같은 제목이 하루에 N번 이상'만 묶음으로 보고, 점수 계산에서는 묶음당 상한(cap)까지만 센다.
묶음은 버리지 않고 리포트에 남기며, AI가 성격(운영사 불만/유저 갈등 등)을 라벨링한다(점수에는 영향 없음)."""
import re
from collections import defaultdict

_NORM = re.compile(r"[^0-9a-z가-힣]")


def norm_title(title: str) -> str:
    return _NORM.sub("", title.lower()) or title


def split_floods(posts, flood_min: int, cap: int):
    """posts → (점수 계산에 쓸 글 목록(묶음은 cap개만, 댓글 많은 순), 묶음 정보 목록)"""
    groups = defaultdict(list)
    for p in posts:
        groups[norm_title(p["title"])].append(p)
    kept, floods = [], []
    for key, items in groups.items():
        if len(items) >= flood_min:
            items.sort(key=lambda p: (p["comment_count"], p["recommend_count"]), reverse=True)
            floods.append({"title": items[0]["title"][:60], "count": len(items),
                           "authors": len({p["author"] for p in items}),
                           "comments": sum(p["comment_count"] for p in items),
                           "sample_post_nos": [p["post_no"] for p in items[:3]]})
            kept.extend(items[:cap])
        else:
            kept.extend(items)
    floods.sort(key=lambda f: f["count"], reverse=True)
    return kept, floods
