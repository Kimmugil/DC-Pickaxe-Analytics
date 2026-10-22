"""AI가 읽기 전에 그날 상위 글의 본문과 댓글을 확실히 가져온다.
수집 봇이 이미 가져온 것은 건너뛰고, 없는 것만 디시에서 읽는다(상위 글 소수만). 차단이 의심되면 즉시 멈추고 있는 만큼으로 분석한다."""
from collector.dc import BlockedError, DC


def ensure_content(conn, dc: DC, g, samples, run, body_top=20, comment_top=8, comment_min=5) -> dict:
    """samples(참여도 순 글)의 본문·댓글을 채운다. 반환: {'bodies': 새로 가져온 본문 수, 'comments': 새로 가져온 댓글 수}"""
    gid, gtype = g["gallery_id"], g["gallery_type"]
    got = {"bodies": 0, "comments": 0}
    try:
        for p in samples[:body_top]:
            if p["body"]:
                continue
            body = dc.fetch_body(gid, gtype, p["post_no"])
            conn.execute("update posts set body = %s, body_fetched_at = now() where gallery_id = %s and post_no = %s",
                         (body, gid, p["post_no"]))
            if body:
                p["body"] = body[:300]
                got["bodies"] += 1
        for p in samples[:comment_top]:
            if p["comment_count"] < comment_min:
                continue
            have = conn.execute("select comments_fetched_at from posts where gallery_id = %s and post_no = %s", (gid, p["post_no"])).fetchone()
            if have and have["comments_fetched_at"]:
                continue
            cms = dc.fetch_comments(gid, gtype, p["post_no"], p["posted_at"], 2)
            if cms:
                with conn.cursor() as cur:
                    cur.executemany(
                        """insert into comments (gallery_id, post_no, comment_no, depth, author, body, posted_at)
                           values (%s,%s,%s,%s,%s,%s,%s) on conflict (gallery_id, post_no, comment_no) do nothing""",
                        [(gid, p["post_no"], c["comment_no"], c["depth"], c["author"], c["body"], c["posted_at"]) for c in cms])
                got["comments"] += len(cms)
            conn.execute("update posts set comments_fetched_at = now() where gallery_id = %s and post_no = %s", (gid, p["post_no"]))
    except BlockedError as e:
        run.note(f"{gid}: 디시 접속 차단 의심({e}) — 가져온 만큼으로 분석합니다", partial=True)
    return got
