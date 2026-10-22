import sys, psycopg
sys.path.insert(0, ".")
from core import config
sys.stdout.reconfigure(encoding="utf-8")
from psycopg.rows import dict_row
with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as c:
    for g, since in (("maplerpg", "2026-09-22"), ("projectcc", "2026-10-01"), ("stoneageia", "2026-09-22"), ("7finger", "2026-09-22")):
        r = c.execute("""
          with d as (select (posted_at at time zone 'Asia/Seoul')::date dd, count(*) n, max(comment_count) top,
                 count(*) filter (where comment_count >= 10) c10, count(*) filter (where comment_count >= 20) c20,
                 count(*) filter (where comment_count >= 30) c30, count(*) filter (where is_best) best
               from posts where gallery_id=%s and source='live' and refresh_stage=2 and not is_notice and posted_at >= %s and posted_at < '2026-10-21'
               group by 1)
          select count(*) days, percentile_cont(array[.25,.5,.75,.9]) within group (order by n) n_q,
                 percentile_cont(array[.25,.5,.75,.9]) within group (order by top) top_q,
                 percentile_cont(array[.25,.5,.75,.9]) within group (order by c10) c10_q,
                 percentile_cont(array[.25,.5,.75,.9]) within group (order by c20) c20_q,
                 percentile_cont(array[.25,.5,.75,.9]) within group (order by c30) c30_q,
                 percentile_cont(array[.25,.5,.75,.9]) within group (order by best) best_q from d""", (g, since)).fetchone()
        f = lambda q: [round(x) for x in q]
        print(g, r["days"], "일 | 게시량", f(r["n_q"]), "| 최다댓글", f(r["top_q"]), "| 댓글10+개수", f(r["c10_q"]), "| 20+", f(r["c20_q"]), "| 30+", f(r["c30_q"]), "| 개념글", f(r["best_q"]), " (25/50/75/90분위)")
