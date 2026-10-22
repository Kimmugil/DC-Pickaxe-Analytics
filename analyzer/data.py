"""분석용 데이터 읽기. 일 단위는 한국시간(KST) 기준.
'유효 게시량' = 공지·반복글(쿠폰 등)을 뺀 글 수에서, 같은 제목 반복(도배) 묶음을 상한까지만 센 값."""
from datetime import date, timedelta

from core import db

KEY_SQL = "coalesce(nullif(regexp_replace(lower(title), '[^0-9a-z가-힣]', '', 'g'), ''), title)"


def daily_counts(conn, gid, start: date, end: date):
    """start~end(포함) 일별 {day: {raw, effective, flood_removed, completeness}}"""
    flood_min = db.setting(conn, "analyzer.flood_min")
    cap = db.setting(conn, "analyzer.flood_cap")
    rows = conn.execute(
        f"""with p as (select (posted_at at time zone 'Asia/Seoul')::date d, {KEY_SQL} k from posts
                       where gallery_id = %(g)s and not is_notice and not is_repetitive
                         and posted_at >= %(s)s::date::timestamp at time zone 'Asia/Seoul'
                         and posted_at <  (%(e)s::date + 1)::timestamp at time zone 'Asia/Seoul'),
                 g as (select d, k, count(*) n from p group by d, k)
            select g.d, sum(n)::int raw,
                   coalesce(sum(case when n >= %(fm)s then n - %(cap)s else 0 end), 0)::int removed,
                   max(c.completeness) completeness
            from g left join daily_coverage c on c.gallery_id = %(g)s and c.day = g.d
            group by g.d order by g.d""",
        {"g": gid, "s": start, "e": end, "fm": flood_min, "cap": cap}).fetchall()
    return {r["d"]: {"raw": r["raw"], "removed": r["removed"], "effective": r["raw"] - r["removed"],
                     "completeness": float(r["completeness"]) if r["completeness"] is not None else None}
            for r in rows}


def day_posts(conn, gid, d: date):
    """그날 글(공지·반복글 제외) 전체. 도배 묶음 처리는 flood.py 에서."""
    return conn.execute(
        """select post_no, title, left(coalesce(body, ''), 300) body, author, comment_count, view_count,
                  recommend_count, is_best, url, posted_at
           from posts where gallery_id = %s and not is_notice and not is_repetitive
             and posted_at >= %s::date::timestamp at time zone 'Asia/Seoul'
             and posted_at <  (%s::date + 1)::timestamp at time zone 'Asia/Seoul'""", (gid, d, d)).fetchall()


def top_comments(conn, gid, post_nos, per_post=6):
    """화제 글의 댓글 일부(좋은 근거 자료). 너무 짧은 댓글은 제외."""
    if not post_nos:
        return {}
    rows = conn.execute(
        """select post_no, body from (
             select post_no, body, row_number() over (partition by post_no order by length(body) desc) rn
             from comments where gallery_id = %s and post_no = any(%s) and length(body) >= 8) t
           where rn <= %s""", (gid, list(post_nos), per_post)).fetchall()
    out = {}
    for r in rows:
        out.setdefault(r["post_no"], []).append(r["body"][:140])
    return out


def reliable_baseline(counts: dict, target: date, weekday_weeks=4, min_ratio=0.7):
    """target 이전 기록에서 기준선을 만든다. 완성도가 평소보다 크게 낮은 날은 제외.
    반환: avg_7d, avg_same_weekday, momentum_avg, n_days(사용한 일수)"""
    comps = sorted(v["completeness"] for v in counts.values() if v["completeness"] is not None)
    median = comps[len(comps) // 2] if comps else None

    def ok(day):
        v = counts.get(day)
        if v is None:
            return False
        if median is None or v["completeness"] is None:
            return True
        return v["completeness"] >= median * min_ratio

    prev7 = [counts[target - timedelta(days=i)]["effective"] for i in range(1, 8) if ok(target - timedelta(days=i))]
    same = [counts[target - timedelta(weeks=w)]["effective"] for w in range(1, weekday_weeks + 1) if ok(target - timedelta(weeks=w))]
    recent = [counts[target - timedelta(days=i)]["effective"] for i in range(1, 4) if ok(target - timedelta(days=i))]
    avg = lambda xs: (sorted(xs)[len(xs) // 2] if len(xs) % 2 else sum(sorted(xs)[len(xs) // 2 - 1:len(xs) // 2 + 1]) / 2) if xs else 0.0   # 중앙값: 과거의 폭증일에 기준선이 끌려가지 않게
    return {"avg_7d": avg(prev7), "avg_same_weekday": avg(same), "momentum_avg": avg(recent), "n_days": len(prev7)}


def comment_baseline(conn, gid, day: date, days=28, min_days=7):
    """최근 days일 중 숫자가 최종값(refresh_stage=2)인 글로 '평소 수준'을 만든다. 기록이 부족하면 None.
    옛 시스템에서 이관한 글은 숫자가 낮게 고정된 값이라 쓰지 않는다(source='live'만)."""
    r = conn.execute(
        """with p as (select (posted_at at time zone 'Asia/Seoul')::date d, comment_count c, is_best from posts
                      where gallery_id = %(g)s and source = 'live' and refresh_stage = 2 and not is_notice and not is_repetitive
                        and posted_at >= (%(d)s::date - %(n)s)::timestamp at time zone 'Asia/Seoul'
                        and posted_at <  %(d)s::date::timestamp at time zone 'Asia/Seoul'),
                t as (select d, max(c) top, count(*) filter (where is_best) best, count(*) cnt from p group by d)
           select (select percentile_cont(0.99) within group (order by c) from p) h99, count(*) days,
                  percentile_cont(0.5) within group (order by top) top_med,
                  percentile_cont(0.5) within group (order by best) best_med, avg(cnt) avg_posts from t""",
        {"g": gid, "d": day, "n": days}).fetchone()
    if not r or (r["days"] or 0) < min_days:
        return None
    return {"hot_threshold": max(5.0, float(r["h99"] or 0)), "top_median": float(r["top_med"] or 1),
            "best_median": float(r["best_med"] or 0), "avg_posts": float(r["avg_posts"] or 0), "days": r["days"]}


def range_posts(conn, gid, start: date, end: date, n=200):
    """기간 내 참여도 상위 n개 글 (공지·반복글 제외). 주간 요약용."""
    return conn.execute(
        """select post_no, title, left(coalesce(body, ''), 300) body, author, comment_count, view_count,
                  recommend_count, is_best, url, posted_at from posts
           where gallery_id = %s and not is_notice and not is_repetitive
             and posted_at >= %s::date::timestamp at time zone 'Asia/Seoul'
             and posted_at <  (%s::date + 1)::timestamp at time zone 'Asia/Seoul'
           order by comment_count * 3 + recommend_count * 2 + view_count * 0.05 + case when is_best then 12 else 0 end desc
           limit %s""", (gid, start, end, n)).fetchall()


def keyword_totals(conn, gid, start: date, end: date, n=10):
    return [[r["keyword"], r["s"]] for r in conn.execute(
        """select keyword, sum(count)::int s from keyword_daily where gallery_id = %s and day between %s and %s
           group by keyword order by s desc limit %s""", (gid, start, end, n)).fetchall()]
