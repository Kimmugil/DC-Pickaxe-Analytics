"""이슈 점수 (최대 10점). 모든 항목을 '그 갤러리의 평소'와 비교한다 (규모가 다른 갤러리를 같은 잣대로 재지 않기 위해).

① 게시량 급증 0~4   — 같은 요일 4주 평균(없으면 7일 평균) 대비 배수와 증가량
② 단일 글 화제성 0~3 — 그날 최다 댓글 ÷ 최근 28일 '하루 최다 댓글'의 중앙값
③ 화제 글 수 0~3     — 평소 상위 1% 수준(최근 28일)을 넘긴 글이 기대치의 몇 배인지
④ 모멘텀 +1          — 최근 3일 평균도 기준선보다 30% 이상 높음
⑤ 개념글 +1          — 개념글 수가 평소 중앙값의 2배 이상(3개 이상)
②③⑤는 숫자가 최종값으로 갱신된 최근 28일 기록(7일 이상)이 있어야 계산한다. 없으면 0점 처리하고 표시만 남긴다."""


def engagement(p) -> float:
    return p["comment_count"] * 3 + p["recommend_count"] * 2 + p["view_count"] * 0.05 + (12 if p["is_best"] else 0)


def _bucket(x, cuts):
    return sum(1 for c in cuts if x >= c)


def issue_score(posts, effective_count, base, has_history: bool, cbase) -> tuple[int, dict]:
    """posts: 도배 묶음 처리가 끝난 그날 글. cbase: data.comment_baseline() 결과 또는 None."""
    baseline = base["avg_same_weekday"] if base["avg_same_weekday"] > 0 else base["avg_7d"]
    parts = {"volume": 0, "top_post": 0, "viral": 0, "momentum": 0, "best": 0}

    if has_history and baseline > 0:
        ratio, delta = effective_count / baseline, effective_count - baseline
        min_delta = max(3.0, baseline * 0.3)
        if ratio >= 3.0 and delta >= min_delta * 2:
            parts["volume"] = 4
        elif ratio >= 2.5 and delta >= min_delta * 1.5:
            parts["volume"] = 3
        elif ratio >= 2.0 and delta >= min_delta:
            parts["volume"] = 2
        elif ratio >= 1.5 and delta >= min_delta * 0.5:
            parts["volume"] = 1
        if base["momentum_avg"] > baseline * 1.3:
            parts["momentum"] = 1

    if cbase and posts:
        top = max(p["comment_count"] for p in posts)
        parts["top_post"] = _bucket(top / max(cbase["top_median"], 1), (1.6, 2.2, 3.2)) if (top >= 10 and len(posts) >= 5) else 0   # 절대 하한(글 수·댓글 수): 작은 갤러리의 잡음 방지
        hot = sum(1 for p in posts if p["comment_count"] >= cbase["hot_threshold"])
        expected = max(1.0, cbase["avg_posts"] * 0.01)
        parts["viral"] = _bucket(hot / expected, (2, 3.5, 6)) if (hot >= 2 and len(posts) >= 5) else 0
        best = sum(1 for p in posts if p["is_best"])
        parts["best"] = 1 if best >= 3 and best >= 2 * max(cbase["best_median"], 1) else 0
    return min(sum(parts.values()), 10), parts
