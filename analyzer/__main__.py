"""분석 실행.  python -m analyzer <명령> [옵션]

  daily      일간 분석     --date D (기본: 어제) [--to D2]   점수·키워드는 항상, AI 요약은 이슈/경계 갤러리만
  weekly     주간 분석     --week-start 월요일 (기본: 지난주)
  monthly    월간 분석     --month YYYY-MM (기본: 지난달)
  calibrate  점수 분포만 확인 (저장·AI 없음)  --from D --to D2
공통: --gallery ID(여러 번)  --no-ai(AI 없이 점수만)
"""
import argparse
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from collector.dc import DC
from core import config, db
from . import ai as aim, daily, keywords as kw, monthly, weekly

KST = timezone(timedelta(hours=9))


def _d(s):
    return date.fromisoformat(s)


def _galleries(conn, only):
    rows = conn.execute("select gallery_id, name, short_name, gallery_type, notes, issue_threshold_adjust, min_issue_posts from galleries where is_active order by gallery_id").fetchall()
    rows = [g for g in rows if not only or g["gallery_id"] in only]
    terms = [t.strip().split()[0] for g in rows for t in (g["notes"] or "").splitlines()
             if t.strip() and not t.strip().startswith("#")]
    kw.register_terms([t.split(":")[0].split("=")[0] for t in terms])     # 용어사전의 단어를 형태소 분석기에 등록
    return rows


def _make_ai(conn, no_ai, run):
    if no_ai:
        return None
    try:
        return aim.AI(conn)
    except aim.AIUnavailable as e:
        run.note(f"AI 없이 진행: {e}", partial=True)
        return None


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="analyzer")
    ap.add_argument("cmd", choices=["daily", "weekly", "monthly", "calibrate"])
    ap.add_argument("--date"); ap.add_argument("--to"); ap.add_argument("--from", dest="frm")
    ap.add_argument("--week-start"); ap.add_argument("--month")
    ap.add_argument("--gallery", action="append", default=[])
    ap.add_argument("--no-ai", action="store_true")
    ap.add_argument("--no-fetch", action="store_true", help="AI 분석 전 본문·댓글을 디시에서 가져오는 단계를 건너뜀")
    a = ap.parse_args(argv)
    conn = db.connect()
    today = datetime.now(KST).date()

    if a.cmd == "calibrate":
        return _calibrate(conn, _galleries(conn, a.gallery), _d(a.frm), _d(a.to))

    with db.JobRun(conn, a.cmd) as run:
        gals = _galleries(conn, a.gallery)
        ai = _make_ai(conn, a.no_ai, run)
        try:
            if a.cmd == "daily":
                start = _d(a.date) if a.date else today - timedelta(days=1)
                end = _d(a.to) if a.to else start
                dc = None if (a.no_ai or a.no_fetch or ai is None) else DC()
                day, n_issue, n = start, 0, 0
                while day <= end:                                  # 날짜 순서대로(키워드 기준선이 쌓이므로)
                    for g in gals:
                        row = daily.run_day(conn, g, day, ai, run, dc=dc)
                        if row:
                            n += 1
                            n_issue += row["has_issue"]
                    day += timedelta(days=1)
                run.processed = n
                run.note(f"일간 {start}~{end}: {n}건 저장, 이슈 {n_issue}건" + (f", AI 호출 {ai.calls}회" if ai else ", AI 없음"))
            elif a.cmd == "weekly":
                ws = _d(a.week_start) if a.week_start else today - timedelta(days=today.weekday() + 7)
                weekly.run_week(conn, ws, gals, ai, run)
            else:
                if a.month:
                    y, m = map(int, a.month.split("-"))
                else:
                    first = today.replace(day=1) - timedelta(days=1)
                    y, m = first.year, first.month
                monthly.run_month(conn, y, m, gals, ai, run)
        except aim.AIUnavailable as e:
            run.note(f"AI 한도/오류로 중단: {e}", partial=True)
        print("완료 · " + "; ".join(run._notes)[:800])
    return 0


def _calibrate(conn, gals, start, end) -> int:
    print(f"점수 분포 {start} ~ {end} (저장·AI 없음)")
    for g in gals:
        n = issue = border = 0
        dist, parts_sum, tops = Counter(), Counter(), []
        day = start
        while day <= end:
            r = daily.compute(conn, g, day)
            day += timedelta(days=1)
            if r is None or r["today"]["raw"] == 0:
                continue
            n += 1
            issue += r["has_issue"]
            border += r["is_borderline"]
            dist[r["score"]] += 1
            parts_sum.update(r["parts"])
            tops.append((r["score"], r["day"], r["today"]["raw"], r["today"]["removed"], round(r["baseline"]), r["parts"],
                         r["top"][0]["comment_count"] if r["top"] else 0, r["low_quality"], r["has_history"]))
        if not n:
            continue
        print(f"\n## {g['name']} ({g['gallery_id']})  {n}일: 이슈 {issue}일({100*issue//n}%) · 경계 {border}일  점수분포 {dict(sorted(dist.items()))}")
        for t in sorted(tops, reverse=True)[:3]:
            print(f"   {t[0]}점 {t[1]} 게시 {t[2]}건(도배 제외 {t[3]}) 기준선 {t[4]} 최다댓글 {t[6]} {t[5]}"
                  f"{' ⚠완성도낮음' if t[7] else ''}{'' if t[8] else ' ⚠기준선부족'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
