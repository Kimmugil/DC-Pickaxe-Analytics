"""주간 분석: 갤러리마다 따로, 그 주에 유저 관심이 가장 컸던 주제를 순위로 정리한다. (갤러리 전체 종합은 만들지 않는다)"""
import uuid
from datetime import date, timedelta

from . import ai as aim, data, flood, issues as iss, store


def _dedupe(posts):
    seen, out = set(), []
    for p in posts:
        k = flood.norm_title(p["title"])
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def period_days(conn, gid, start: date, end: date):
    """기간 중 일간 리포트(온도 판정과 헤드라인). 화면의 '평소와 달랐던 날' 목록과 AI 입력에 쓴다."""
    return conn.execute(
        """select to_char(period_start, 'YYYY-MM-DD') as day, issue_score, has_issue, is_borderline, headline, post_count,
                  (extra is not null) as modern, extra
           from reports where period_type = 'day' and gallery_id = %s and period_start between %s and %s order by period_start""",
        (gid, start, end)).fetchall()


def day_chips(days):
    return [{"day": d["day"], "issue": bool(d["has_issue"]), "watch": bool(d["is_borderline"]), "score": d["issue_score"],
             "modern": bool(d["modern"]), "headline": d["headline"]} for d in days if d["has_issue"] or d["is_borderline"]]


def run_week(conn, week_start: date, galleries, ai, run, write=True):
    week_end = week_start + timedelta(days=6)
    label = f"{week_start} ~ {week_end}"
    run_id = f"week-{week_start}-{uuid.uuid4().hex[:6]}"
    rows = []
    for g in galleries:
        gid = g["gallery_id"]
        counts = data.daily_counts(conn, gid, week_start, week_end)
        total = sum(v["raw"] for v in counts.values())
        if total == 0:
            continue
        posts = _dedupe(data.range_posts(conn, gid, week_start, week_end, n=20000))
        keywords = data.keyword_totals(conn, gid, week_start, week_end)
        days = period_days(conn, gid, week_start, week_end)
        floods = [f for d in days for f in ((d["extra"] or {}).get("floods") or [])]
        floods.sort(key=lambda f: f.get("count", 0), reverse=True)
        daily_lines = "\n".join(f"- {d['day']}: {d['headline']}" for d in days if d["has_issue"] and d["headline"])
        res = {}
        if ai is not None and total >= 10:
            res = aim.clean_structured(limit=5, raw=ai.call_json(aim.week_prompt(g, label, total, daily_lines, posts[:40], keywords, floods)))
            res["major_issues"] = iss.finalize_issues(res["major_issues"], {p["post_no"]: p for p in posts}, posts)
        row = {"period_type": "week", "period_start": week_start, "period_end": week_end, "gallery_id": gid,
               "post_count": total, "headline": res.get("headline") or None,
               "summary": res.get("summary") or ("(이 주의 게시글이 10건 미만이라 요약하지 않았습니다)" if total < 10 else None),
               "major_issues": res.get("major_issues"),
               "top_posts": [store.top_post_view(p) for p in store.most_discussed(posts)[:5]],
               "keywords": keywords, "daily_counts": {str(d): v["raw"] for d, v in sorted(counts.items())},
               "run_id": run_id, "extra": {"issue_days": sum(1 for d in days if d["has_issue"]), "days": day_chips(days), "floods": floods[:5]}}
        rows.append(row)
    if write:
        for row in rows:
            store.save_report(conn, row)
    run.processed += len(rows)
    run.note(f"주간 {label}: 갤러리 {len(rows)}개")
    return rows
