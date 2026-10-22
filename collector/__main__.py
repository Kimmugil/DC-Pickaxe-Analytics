"""실행 진입점.  python -m collector <명령> [옵션]

  run        정기 실행(새 글 → 숫자 갱신 → 본문·댓글 → 완성도). 스케줄러가 이걸 부른다
  scrape     새 글 수집만      refresh   숫자 갱신만      enrich   본문·댓글만     coverage  완성도만
  history    과거 글 채우기 (--gallery ID --pages N)
  detect     갤러리 종류 판별 (--gallery ID)
  thumbs     갤러리 대표 이미지 가져오기 (없는 것만, --force 면 전부 다시)
공통 옵션: --gallery ID(여러 번 가능)  --force(주기 무시)
"""
import argparse
import sys
from datetime import datetime, timedelta, timezone

from core import db
from .coverage import run_coverage
from .dc import DC, BlockedError
from .enrich import enrich_bodies, enrich_comments
from .refresh import run_refresh
from .scrape import run_history, run_scrape
from .thumbs import run_thumbs


def _blocked_until(conn):
    v = db.setting(conn, "collector.blocked_until", cast=str)
    if not v:
        return None
    try:
        t = datetime.fromisoformat(v)
        return t if t > datetime.now(timezone.utc) else None
    except ValueError:
        return None


def _on_blocked(conn):
    n = int(db.setting(conn, "collector.block_count", cast=str) or 0) + 1
    base = db.setting(conn, "collector.cooldown_base_min")
    minutes = min(360, base * 2 ** (n - 1))
    db.set_setting(conn, "collector.block_count", n)
    db.set_setting(conn, "collector.blocked_until", (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat())
    return minutes


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="collector")
    ap.add_argument("cmd", choices=["run", "scrape", "refresh", "enrich", "coverage", "history", "detect", "thumbs"])
    ap.add_argument("--gallery", action="append", default=[])
    ap.add_argument("--pages", type=int, default=30)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    only = a.gallery or None

    conn = db.connect()
    until = _blocked_until(conn)
    if until and not a.force and a.cmd != "coverage":
        print(f"차단 대기 중 — {until.astimezone().strftime('%m-%d %H:%M')} 까지 쉽니다.")
        return 0

    dc = DC()
    job = {"run": "run", "scrape": "scrape", "refresh": "refresh", "enrich": "enrich", "coverage": "coverage",
           "history": "history", "detect": "detect", "thumbs": "thumbs"}[a.cmd]
    try:
        with db.JobRun(conn, job, only[0] if only and len(only) == 1 else None) as run:
            if a.cmd == "detect":
                for gid in only or []:
                    print(gid, "→", dc.detect_type(gid))
                return 0
            if a.cmd == "history":
                if len(only or []) != 1:
                    sys.exit("history 는 --gallery 를 하나 지정해야 합니다")
                run_history(dc, conn, run, only[0], a.pages)
            if a.cmd in ("run", "scrape"):
                run_scrape(dc, conn, run, only, a.force)
            if a.cmd in ("run", "refresh"):
                run_refresh(dc, conn, run, only, a.force)
            if a.cmd in ("run", "enrich"):
                enrich_bodies(dc, conn, run)
                enrich_comments(dc, conn, run)
            if a.cmd in ("run", "thumbs"):
                run_thumbs(dc, conn, run, only, a.force and a.cmd == "thumbs")
            if a.cmd in ("run", "coverage"):
                run_coverage(conn, run)
            db.set_setting(conn, "collector.block_count", 0)
            print(f"완료 · 요청 {dc.n_requests}회 · " + "; ".join(run._notes)[:600])
    except BlockedError as e:
        minutes = _on_blocked(conn)
        print(f"⚠ 차단 의심({e}) — {minutes}분 쉽니다.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
