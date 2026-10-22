"""새 글 수집 + 누락 구간 따라잡기 + 과거 글 채우기.

핵심: 1페이지부터 훑다가 이미 저장된 글을 5개 연속 만나면 "여기부터는 수집 완료"로 보고 멈춘다.
정기 수집에서 못 끝나면(= 누락 구간이 길면) 다음 실행에서 이어서 따라잡는다.
본문은 여기서 가져오지 않는다(요청 수 절감). 반응이 있는 글만 enrich 단계에서 가져온다.
"""
import random
import re
from datetime import datetime, timedelta, timezone

from core import db
from .dc import DC, BlockedError, post_url

ROWS_PER_PAGE = 50    # 깊은 페이지 기준(1페이지는 공지 때문에 40)
KNOWN_STOP = 5

INSERT_SQL = """
insert into posts (gallery_id, post_no, title, author, posted_at, posted_time_known, url,
                   comment_count, view_count, recommend_count, refresh_stage, metrics_updated_at,
                   is_repetitive, is_best, source)
values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,'live')
on conflict (gallery_id, post_no) do nothing
"""


def load_rules(conn):
    rows = conn.execute("select pattern from noise_rules where enabled and kind = 'title_regex'").fetchall()
    out = []
    for r in rows:
        try:
            out.append(re.compile(r["pattern"], re.I))
        except re.error:
            continue    # 잘못된 규칙은 건너뜀(관리자 페이지에서 검증 예정)
    return out


def is_repetitive(title, rules) -> bool:
    return any(r.search(title) for r in rules)


def collect(dc: DC, conn, g, rules, start_page, max_pages, stop_on_known=True, require_new_first=False) -> dict:
    """start_page부터 최대 max_pages장 수집. 결과: inserted, reached_known, empty, last_page, head_no
    require_new_first: 이어받기 때 시작 부분에 겹치는 기존 글이 있어도 멈추지 않고, 새 글을 한 번 만난 뒤부터 멈춤 판정"""
    gid, gtype = g["gallery_id"], g["gallery_type"]
    final_after = timedelta(hours=db.setting(conn, "collector.refresh_stage2_h"))
    now = datetime.now(timezone.utc)
    inserted, consecutive, head_no, new_in_run = 0, 0, None, set()
    reached, empty, page = False, False, start_page
    while page < start_page + max_pages:
        rows = [r for r in dc.list_page(gid, gtype, page) if not r.is_notice]
        if not rows:
            empty = True
            break
        if head_no is None:
            head_no = max(r.post_no for r in rows)
        nos = [r.post_no for r in rows]
        have = {x["post_no"] for x in conn.execute(
            "select post_no from posts where gallery_id = %s and post_no = any(%s)", (gid, nos)).fetchall()}
        batch = []
        for r in rows:
            if r.post_no in new_in_run:        # 수집 중 페이지가 밀려 같은 글이 또 나온 경우
                continue
            if r.post_no in have:
                consecutive += 1
                if stop_on_known and consecutive >= KNOWN_STOP and (new_in_run or not require_new_first):
                    reached = True
                    break
                continue
            consecutive = 0
            new_in_run.add(r.post_no)
            batch.append((gid, r.post_no, r.title, r.author, r.posted_at, r.time_known, post_url(gtype, gid, r.post_no),
                          r.comment_count, r.view_count, r.recommend_count,
                          2 if now - r.posted_at >= final_after else 0,   # 이미 오래된 글(따라잡기)은 숫자가 최종값
                          is_repetitive(r.title, rules), r.is_best))
        if batch:
            with conn.cursor() as cur:
                cur.executemany(INSERT_SQL, batch)
            inserted += len(batch)
        if reached:
            break
        page += 1
    return {"inserted": inserted, "reached_known": reached, "empty": empty, "last_page": page, "head_no": head_no}


def _cursor(conn, gid, kind):
    return conn.execute("select * from crawl_cursor where gallery_id = %s and kind = %s", (gid, kind)).fetchone()


def _save_cursor(conn, gid, kind, last_page, head_no, added, done):
    conn.execute(
        """insert into crawl_cursor (gallery_id, kind, last_page, head_no, collected_count, done)
           values (%s,%s,%s,%s,%s,%s)
           on conflict (gallery_id, kind) do update set last_page = excluded.last_page, head_no = excluded.head_no,
             collected_count = crawl_cursor.collected_count + excluded.collected_count, done = excluded.done, updated_at = now()""",
        (gid, kind, last_page, head_no, added, done))


def _resume_page(cur, head_no, floor) -> int:
    """이전에 멈춘 페이지에서 이어가되, 그 사이 새 글이 쌓여 밀린 만큼 앞으로 당긴다."""
    if not cur or cur["last_page"] <= 0:
        return floor
    drift = max(0, ((head_no or 0) - (cur["head_no"] or 0)) // ROWS_PER_PAGE)
    return max(floor, cur["last_page"] - drift - 1)


def scrape_gallery(dc, conn, g, rules) -> str:
    gid = g["gallery_id"]
    head_pages = db.setting(conn, "collector.head_pages")
    n_posts = conn.execute("select count(*) as n from posts where gallery_id = %s", (gid,)).fetchone()["n"]

    if n_posts == 0:      # 새 갤러리: 맛보기만. 과거 글은 history(backfill)로 따로 채운다
        res = collect(dc, conn, g, rules, 1, db.setting(conn, "collector.initial_pages"), stop_on_known=False)
        return f"신규 갤러리 첫 수집 {res['inserted']}개"

    head = collect(dc, conn, g, rules, 1, head_pages)
    added = head["inserted"]
    cur = _cursor(conn, gid, "catchup")
    if head["empty"]:
        conn.execute("delete from crawl_cursor where gallery_id = %s and kind = 'catchup'", (gid,))
        return f"{added}개 수집" if added else "새 글 없음"
    if head["reached_known"] and cur is None:      # 평소: 앞쪽만 보면 충분
        return f"{added}개 수집" if added else "새 글 없음"

    # 누락 구간이 큼(정기 범위 안에서 기존 글을 못 만남) 또는 이전 따라잡기가 남아 있음 → 이어서 따라잡기
    # (앞쪽이 이미 저장돼 있어도, 저장된 진행 위치가 있으면 그 아래 구간은 아직 비어 있는 것)
    start = _resume_page(cur, head["head_no"], head_pages + 1)
    cu = collect(dc, conn, g, rules, start, db.setting(conn, "collector.catchup_pages"), require_new_first=True)
    added += cu["inserted"]
    if cu["reached_known"] or cu["empty"]:
        conn.execute("delete from crawl_cursor where gallery_id = %s and kind = 'catchup'", (gid,))
        return f"{added}개 수집 (누락 구간 따라잡기 완료)"
    _save_cursor(conn, gid, "catchup", cu["last_page"], head["head_no"], cu["inserted"], False)
    return f"{added}개 수집 (누락 구간 따라잡는 중, 페이지 {cu['last_page']}까지)"


def run_scrape(dc, conn, run, only=None, force=False):
    q = """select * from galleries where is_active
           and (%(force)s or last_collected_at is null
                or last_collected_at <= now() - (collect_interval_min * 0.9) * interval '1 minute')"""
    gals = conn.execute(q, {"force": force}).fetchall()
    if only:
        gals = [g for g in gals if g["gallery_id"] in only]
    random.shuffle(gals)           # 매번 순서를 섞어 요청 패턴을 단조롭게 만들지 않음
    rules = load_rules(conn)
    for g in gals:
        try:
            msg = scrape_gallery(dc, conn, g, rules)
        except BlockedError:
            conn.execute("update galleries set last_collected_at = now(), last_result = %s where gallery_id = %s",
                         ("차단 의심 — 중단", g["gallery_id"]))
            raise
        except Exception as e:     # 한 갤러리 실패가 전체를 막지 않게
            msg = f"에러: {type(e).__name__}"
            run.note(f"{g['gallery_id']}: {e}", partial=True)
        conn.execute("update galleries set last_collected_at = now(), last_result = %s where gallery_id = %s",
                     (msg, g["gallery_id"]))
        run.processed += 1
        run.note(f"{g['gallery_id']} {msg}")


def run_history(dc, conn, run, gid, pages):
    """과거 글 채우기: 마지막으로 멈춘 곳에서 pages장 더 거슬러 올라간다."""
    g = conn.execute("select * from galleries where gallery_id = %s", (gid,)).fetchone()
    if g is None:
        raise ValueError(f"등록되지 않은 갤러리: {gid}")
    rules = load_rules(conn)
    cur = _cursor(conn, gid, "history")
    if cur and cur["done"]:
        run.note("이미 끝까지 수집됨")
        return
    first = [r for r in dc.list_page(gid, g["gallery_type"], 1) if not r.is_notice]
    head_no = max((r.post_no for r in first), default=None)
    start = _resume_page(cur, head_no, 1)
    res = collect(dc, conn, g, rules, start, pages, stop_on_known=False)
    _save_cursor(conn, gid, "history", res["last_page"], head_no, res["inserted"], res["empty"])
    run.processed = res["inserted"]
    run.note(f"{gid} 페이지 {start}~{res['last_page']}: {res['inserted']}개" + (" (끝)" if res["empty"] else ""))
