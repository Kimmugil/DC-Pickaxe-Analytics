"""reports 표 저장 (일간·주간·월간 공통). 같은 기간·갤러리는 덮어쓴다(upsert)."""
from psycopg.types.json import Jsonb

COLS = ["period_type", "period_start", "period_end", "gallery_id", "post_count", "avg_7d", "avg_same_weekday",
        "momentum_avg", "issue_score", "has_issue", "is_borderline", "headline", "summary", "temperature_tag",
        "top_cause", "category_scores", "major_issues", "sentiment", "top_posts", "keywords", "daily_counts",
        "run_id", "extra"]
JSON_COLS = {"category_scores", "major_issues", "sentiment", "top_posts", "keywords", "daily_counts", "extra"}


def save_report(conn, row: dict) -> None:
    row = {"has_issue": False, "is_borderline": False, **row}
    vals = [Jsonb(row.get(c)) if c in JSON_COLS and row.get(c) is not None else row.get(c) for c in COLS]
    conn.execute(
        f"insert into reports ({','.join(COLS)}) values ({','.join(['%s'] * len(COLS))}) "
        "on conflict (period_type, period_start, coalesce(gallery_id, '')) do update set "
        + ",".join(f"{c} = excluded.{c}" for c in COLS[4:]) + ", updated_at = now()", vals)


def most_discussed(posts) -> list:
    """화면의 '인기글'은 가장 많이 논의된(댓글 많은) 글 순. AI 입력용 참여도 순위와는 별개."""
    return sorted(posts, key=lambda p: (p["comment_count"], p["recommend_count"]), reverse=True)


def top_post_view(p) -> dict:
    """화면용 인기글 형식 (예전 데이터와 같은 한글 키)"""
    return {"제목": p["title"], "링크": p["url"], "날짜": p["posted_at"].astimezone().strftime("%Y-%m-%d"),
            "댓글수": p["comment_count"], "추천수": p["recommend_count"], "조회수": p["view_count"],
            "개념글": bool(p["is_best"])}
