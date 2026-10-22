"""월간 분석: 갤러리마다 따로, 그 달에 유저 관심이 가장 컸던 주제를 순위로 정리한다. (갤러리 전체 종합은 만들지 않는다)"""
import calendar
import uuid
from datetime import date

from . import ai as aim, data, issues as iss, store
from .weekly import _dedupe, day_chips, period_days


def run_month(conn, year: int, month: int, galleries, ai, run, write=True):
    start, end = date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
    label = f"{year}-{month:02d}"
    run_id = f"month-{label}-{uuid.uuid4().hex[:6]}"
    rows = []
    for g in galleries:
        gid = g["gallery_id"]
        counts = data.daily_counts(conn, gid, start, end)
        total = sum(v["raw"] for v in counts.values())
        if total == 0:
            continue
        days = period_days(conn, gid, start, end)
        posts = _dedupe(data.range_posts(conn, gid, start, end, n=20000))
        keywords = data.keyword_totals(conn, gid, start, end)
        weekly = conn.execute(
            """select to_char(period_start, 'MM-DD') as s, to_char(period_end, 'MM-DD') as e, headline from reports
               where period_type = 'week' and gallery_id = %s and period_end >= %s and period_start <= %s and headline is not null
               order by period_start""", (gid, start, end)).fetchall()
        weekly_lines = "\n".join(f"- {w['s']}~{w['e']}: {w['headline']}" for w in weekly)
        daily_lines = "\n".join(f"- {d['day']}: {d['headline']}" for d in days if d["has_issue"] and d["headline"])
        res = {}
        if ai is not None and total >= 30:
            res = aim.clean_structured(limit=5, raw=ai.call_json(aim.month_prompt(g, label, total, daily_lines, weekly_lines, posts[:40], keywords)))
            res["major_issues"] = iss.finalize_issues(res["major_issues"], {p["post_no"]: p for p in posts}, posts)
        issue_days = [d for d in days if d["has_issue"]]
        row = {"period_type": "month", "period_start": start, "period_end": end, "gallery_id": gid, "post_count": total,
               "headline": res.get("headline") or None,
               "summary": res.get("summary") or ("(이 달의 게시글이 30건 미만이라 요약하지 않았습니다)" if total < 30 else None),
               "major_issues": res.get("major_issues"),
               "top_posts": [store.top_post_view(p) for p in store.most_discussed(posts)[:5]],
               "keywords": keywords, "daily_counts": {str(d): v["raw"] for d, v in sorted(counts.items())}, "run_id": run_id,
               "extra": {"issue_days": len(issue_days), "days": day_chips(days)}}
        rows.append(row)
    if write:
        for row in rows:
            store.save_report(conn, row)
    run.processed += len(rows)
    run.note(f"월간 {label}: 갤러리 {len(rows)}개")
    return rows
