"""반응이 있는 글에 한해 본문과 댓글 내용을 가져온다 (요청 수를 아끼고 디시 부담을 줄이기 위함)."""
from core import db
from .dc import DC, BlockedError


def enrich_bodies(dc: DC, conn, run) -> int:
    min_c = db.setting(conn, "collector.body_min_comments")
    limit = db.setting(conn, "collector.body_per_run")
    rows = conn.execute(
        """select p.gallery_id, p.post_no, g.gallery_type from posts p join galleries g using (gallery_id)
           where p.source = 'live' and p.refresh_stage >= 1 and p.refresh_stage < 3 and p.body_fetched_at is null
             and not p.is_notice and not p.is_repetitive
             and (p.comment_count >= %s or p.is_best)
           order by (p.posted_at at time zone 'Asia/Seoul')::date desc, p.comment_count desc limit %s""", (min_c, limit)).fetchall()
    done = fails = 0
    for r in rows:
        body = dc.fetch_body(r["gallery_id"], r["gallery_type"], r["post_no"])
        fails = fails + 1 if body is None else 0
        if fails >= 5:
            raise BlockedError("본문 5건 연속 실패")
        conn.execute("update posts set body = %s, body_fetched_at = now() where gallery_id = %s and post_no = %s",
                     (body, r["gallery_id"], r["post_no"]))
        done += body is not None
    run.processed += done
    run.note(f"본문 {done}/{len(rows)}")
    return done


def enrich_comments(dc: DC, conn, run) -> int:
    min_c = db.setting(conn, "collector.comments_min")
    limit = db.setting(conn, "collector.comments_per_run")
    pages = db.setting(conn, "collector.comments_max_pages")
    rows = conn.execute(
        """select p.gallery_id, p.post_no, p.posted_at, g.gallery_type from posts p join galleries g using (gallery_id)
           where p.source = 'live' and p.refresh_stage >= 1 and p.refresh_stage < 3 and p.comments_fetched_at is null
             and not p.is_notice and not p.is_repetitive and (p.comment_count >= %s or p.is_best)
           order by (p.posted_at at time zone 'Asia/Seoul')::date desc, p.comment_count desc limit %s""", (min_c, limit)).fetchall()
    posts = saved = 0
    for r in rows:
        cms = dc.fetch_comments(r["gallery_id"], r["gallery_type"], r["post_no"], r["posted_at"], pages)
        if cms:
            with conn.cursor() as cur:
                cur.executemany(
                    """insert into comments (gallery_id, post_no, comment_no, depth, author, body, posted_at)
                       values (%s,%s,%s,%s,%s,%s,%s) on conflict (gallery_id, post_no, comment_no) do nothing""",
                    [(r["gallery_id"], r["post_no"], c["comment_no"], c["depth"], c["author"], c["body"], c["posted_at"])
                     for c in cms])
            saved += len(cms)
        conn.execute("update posts set comments_fetched_at = now() where gallery_id = %s and post_no = %s",
                     (r["gallery_id"], r["post_no"]))
        posts += 1
    run.processed += posts
    run.note(f"댓글: 글 {posts}개, 댓글 {saved}개")
    return saved
