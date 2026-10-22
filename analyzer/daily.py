"""일간 이슈 분석.
점수·키워드·도배 감지는 DB 숫자만으로 계산(AI 없이도 항상 가능). AI 요약은 이슈/경계 갤러리에만 붙인다."""
import uuid
from datetime import date, timedelta

from core import db
from . import ai as aim, content, data, evidence, flood, issues as iss, keywords as kw, score, store


def _auto_adjust(conn, gid, day: date, base_thr: int) -> int:
    """최근 28일에 기준 점수를 넘은 날이 20%를 넘는 갤러리는 기준을 1점(35% 넘으면 2점) 올린다. (너무 후한 판정 방지)"""
    r = conn.execute(
        """select count(*) n, count(*) filter (where issue_score >= %s) hit from reports
           where period_type = 'day' and gallery_id = %s and period_start >= %s::date - 28 and period_start < %s
             and extra->'score_parts' is not null""",   # 새 방식으로 계산한 리포트만 (이관된 옛 방식 점수는 제외)
        (base_thr, gid, day, day)).fetchone()
    if r["n"] < 14:
        return 0
    rate = r["hit"] / r["n"]
    return 2 if rate > 0.35 else 1 if rate > 0.20 else 0


def compute(conn, g, day: date) -> dict | None:
    gid = g["gallery_id"]
    if conn.execute("select 1 from crawl_cursor where gallery_id = %s and kind = 'catchup' and not done", (gid,)).fetchone():
        return None        # 누락 구간을 따라잡는 중이면 일부 날짜 데이터가 비어 있어 분석을 보류
    counts = data.daily_counts(conn, gid, day - timedelta(days=35), day)
    if not counts:
        return None
    today = counts.get(day, {"raw": 0, "removed": 0, "effective": 0, "completeness": None})
    posts = data.day_posts(conn, gid, day)
    kept, floods = flood.split_floods(posts, db.setting(conn, "analyzer.flood_min"), db.setting(conn, "analyzer.flood_cap"))
    base = data.reliable_baseline(counts, day, min_ratio=db.setting(conn, "analyzer.min_coverage_ratio"))
    has_history = base["n_days"] >= db.setting(conn, "analyzer.min_history_days")
    cbase = data.comment_baseline(conn, gid, day)
    sc, parts = score.issue_score(kept, today["effective"], base, has_history, cbase)
    base_thr, base_border = db.setting(conn, "analyzer.issue_threshold"), db.setting(conn, "analyzer.borderline_threshold")
    auto = _auto_adjust(conn, gid, day, base_thr)
    shift = int(g.get("issue_threshold_adjust") or 0) + auto
    thr, border = base_thr + shift, base_border + shift
    topic, prof = kw.extract(kept)
    rising = kw.rising(conn, gid, day, topic)
    comps = sorted(v["completeness"] for v in counts.values() if v["completeness"] is not None)
    median = comps[len(comps) // 2] if comps else None
    low_quality = (today["completeness"] is not None and median is not None
                   and today["completeness"] < median * db.setting(conn, "analyzer.min_coverage_ratio"))
    baseline = base["avg_same_weekday"] or base["avg_7d"]
    return {"g": g, "day": day, "posts": posts, "kept": kept, "floods": floods, "base": base, "baseline": baseline,
            "has_history": has_history, "cbase": cbase, "score": sc, "parts": parts, "topic": topic, "prof_posts": prof, "rising": rising,
            "today": today, "low_quality": low_quality, "threshold_shift": shift, "auto_shift": auto,
            "has_issue": sc >= thr and today["effective"] >= int(g.get("min_issue_posts") or 0), "is_borderline": border <= sc < thr,
            "top": sorted(kept, key=score.engagement, reverse=True), "counts": counts}


def _ai_issue(conn, ai, r, dc=None, run=None):
    g, day = r["g"], r["day"]
    samples = r["top"][:15]
    if dc is not None:                                        # AI가 읽기 전에 상위 글의 본문·댓글을 확실히 확보
        got = content.ensure_content(conn, dc, g, r["top"][:20], run)
        if run and (got["bodies"] or got["comments"]):
            run.note(f"{g['gallery_id']} {day} 본문 {got['bodies']}개·댓글 {got['comments']}개 새로 가져옴")
    comments = data.top_comments(conn, g["gallery_id"], [p["post_no"] for p in samples[:8]], per_post=5)
    stats = {"count": r["today"]["effective"], "baseline": r["baseline"], "score": r["score"]}
    keywords = r["topic"].most_common(10)
    res = aim.clean_structured(limit=3, raw=ai.call_json(
        aim.daily_issue_prompt(g, day, stats, samples, comments, keywords, r["rising"], r["floods"])))
    by_no = {p["post_no"]: p for p in r["kept"]}
    res["major_issues"] = iss.finalize_issues(res["major_issues"], by_no, r["kept"])
    res["sentiment"] = evidence.verify_sentiment(res.pop("sentiment_raw", {}), by_no, comments)   # 근거가 없으면 비어 있다
    return res


def build_row(r, run_id, ai_res=None):
    day, g = r["day"], r["g"]
    ai_res = ai_res or {}
    raw_counts = {str(d): v["raw"] for d, v in sorted(r["counts"].items())}
    extra = {"score_parts": r["parts"], "effective_count": r["today"]["effective"], "flood_removed": r["today"]["removed"],
             "floods": r["floods"][:5], "rising": r["rising"], "profanity_post_ratio": round(r["prof_posts"] / max(len(r["kept"]), 1), 3),
             "best_count": sum(1 for p in r["posts"] if p["is_best"]), "has_history": r["has_history"],
             "threshold_shift": r["threshold_shift"], "auto_shift": r["auto_shift"],
             "comment_baseline": bool(r["cbase"]),
             "completeness": r["today"]["completeness"], "low_quality": r["low_quality"]}
    return {
        "period_type": "day", "period_start": day, "period_end": day, "gallery_id": g["gallery_id"],
        "post_count": r["today"]["raw"], "avg_7d": round(r["base"]["avg_7d"], 1), "avg_same_weekday": round(r["base"]["avg_same_weekday"], 1),
        "momentum_avg": round(r["base"]["momentum_avg"], 1), "issue_score": r["score"], "has_issue": r["has_issue"],
        "is_borderline": r["is_borderline"],
        "headline": ai_res.get("headline") or None, "summary": ai_res.get("summary") or None,
        "major_issues": ai_res.get("major_issues"), "sentiment": ai_res.get("sentiment"),
        "top_posts": [store.top_post_view(p) for p in store.most_discussed(r["kept"])[:5]],
        "keywords": [[w, c] for w, c in r["topic"].most_common(10)], "daily_counts": raw_counts,
        "run_id": run_id, "extra": extra}


def run_day(conn, g, day: date, ai, run, write=True, dc=None):
    r = compute(conn, g, day)
    if r is None or (r["today"]["raw"] == 0 and sum(v["raw"] for v in r["counts"].values()) == 0):
        return None
    run_id = f"day-{day}-{uuid.uuid4().hex[:6]}"
    ai_res = None
    if ai is not None and r["has_issue"]:          # AI 요약은 이슈인 날에만 (평온·주목인 날은 숫자와 키워드만)
        try:
            ai_res = _ai_issue(conn, ai, r, dc, run)
        except aim.AIUnavailable as e:
            run.note(f"AI 중단: {e}", partial=True)
            raise
        except Exception as e:
            import traceback
            tb = traceback.extract_tb(e.__traceback__)[-1]
            run.note(f"{g['gallery_id']} {day} AI 처리 실패: {type(e).__name__}: {e} ({tb.filename.split(chr(92))[-1]}:{tb.lineno})", partial=True)
    row = build_row(r, run_id, ai_res)
    if write:
        store.save_report(conn, row)
        kw.save_daily(conn, g["gallery_id"], day, r["topic"])
    return row
