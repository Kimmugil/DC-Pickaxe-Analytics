"""숫자 갱신: 글이 올라온 뒤 N시간 지난 글의 댓글·조회·추천수를 최신 값으로 덮어쓴다.
개념글 표시, 나중에 공지로 고정된 글 표시, 끝내 확인 못한 글(삭제 추정) 마무리도 여기서 한다."""
from datetime import datetime, timedelta, timezone

from core import db
from .dc import DC

SCAN_LIMIT_PAGES = 80          # 한 갤러리당 한 번에 훑는 최대 페이지 (글이 아주 많은 갤러리 보호)
BEST_PAGES = 3


def refresh_gallery(dc: DC, conn, g) -> str:
    gid, gtype = g["gallery_id"], g["gallery_type"]
    h1 = db.setting(conn, "collector.refresh_stage1_h")
    h2 = db.setting(conn, "collector.refresh_stage2_h")
    now = datetime.now(timezone.utc)
    stop_before = now - timedelta(hours=h2 + 24)      # 이보다 오래된 글만 있는 페이지가 나오면 멈춤

    updated = notices = 0
    for page in range(1, SCAN_LIMIT_PAGES + 1):
        rows = dc.list_page(gid, gtype, page)
        regular = [r for r in rows if not r.is_notice]
        if not rows:
            break
        # 공지로 고정된 글: 분석에서 제외하기 위해 표시
        for r in rows:
            if r.is_notice:
                notices += conn.execute(
                    "update posts set is_notice = true where gallery_id = %s and post_no = %s and not is_notice",
                    (gid, r.post_no)).rowcount
        if regular:
            have = {x["post_no"]: x for x in conn.execute(
                "select post_no, posted_at, refresh_stage from posts "
                "where gallery_id = %s and post_no = any(%s) and source = 'live' and refresh_stage < 2",
                (gid, [r.post_no for r in regular])).fetchall()}
            updates = []
            for r in regular:
                p = have.get(r.post_no)
                if not p:
                    continue
                age_h = (now - p["posted_at"]).total_seconds() / 3600
                stage = 2 if age_h >= h2 else (1 if age_h >= h1 and p["refresh_stage"] == 0 else None)
                if stage:
                    updates.append((r.comment_count, r.view_count, r.recommend_count, stage, gid, r.post_no))
            if updates:
                with conn.cursor() as cur:
                    cur.executemany(
                        "update posts set comment_count=%s, view_count=%s, recommend_count=%s, refresh_stage=%s, "
                        "metrics_updated_at=now() where gallery_id=%s and post_no=%s", updates)
                updated += len(updates)
            if all(r.posted_at < stop_before for r in regular):
                break

    # 개념글 탭: 최근 개념글 표시
    best = 0
    for page in range(1, BEST_PAGES + 1):
        rows = [r for r in dc.list_page(gid, gtype, page, recommend=True) if not r.is_notice]
        if not rows:
            break
        best += conn.execute(
            "update posts set is_best = true where gallery_id = %s and post_no = any(%s) and not is_best",
            (gid, [r.post_no for r in rows])).rowcount

    # 오래돼도 끝내 목록에서 못 본 글 = 삭제된 것으로 추정하고 갱신 대상에서 뺀다
    lost = conn.execute(
        "update posts set refresh_stage = 3 where gallery_id = %s and source = 'live' and refresh_stage < 2 "
        "and posted_at < now() - make_interval(hours => %s)", (gid, h2 + 24)).rowcount

    conn.execute("update galleries set last_refreshed_at = now() where gallery_id = %s", (gid,))
    return f"갱신 {updated} · 개념글 +{best} · 공지전환 {notices} · 삭제추정 {lost}"


def run_refresh(dc, conn, run, only=None, force=False):
    every = db.setting(conn, "collector.refresh_every_h")
    gals = conn.execute(
        """select * from galleries where is_active
           and (%(force)s or last_refreshed_at is null or last_refreshed_at <= now() - make_interval(hours => %(h)s))
           order by random()""", {"force": force, "h": every}).fetchall()
    if only:
        gals = [g for g in gals if g["gallery_id"] in only]
    for g in gals:
        try:
            msg = refresh_gallery(dc, conn, g)
        except Exception as e:
            if type(e).__name__ == "BlockedError":
                raise
            msg = f"에러: {type(e).__name__}"
            run.note(f"{g['gallery_id']}: {e}", partial=True)
        run.processed += 1
        run.note(f"{g['gallery_id']} {msg}")
