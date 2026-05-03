"""
주간 분석 백필 스크립트

지정 기간의 모든 주(월요일 기준)를 순서대로 분석해 weekly_galleries / weekly_overall 시트에 적재합니다.

사용법:
  python backfill_weekly.py --start 2026-01-05 --end 2026-04-28
  python backfill_weekly.py --start 2026-01-05 --end 2026-04-28 --dry-run
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()


def get_mondays(start: str, end: str) -> list[str]:
    """start~end 사이의 모든 월요일 날짜 반환 (포함)"""
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    # 첫 번째 월요일로 이동 (weekday: 0=월요일)
    if d0.weekday() != 0:
        d0 = d0 + timedelta(days=(7 - d0.weekday()) % 7)
    mondays = []
    cur = d0
    while cur <= d1:
        mondays.append(cur.isoformat())
        cur += timedelta(days=7)
    return mondays


def main() -> None:
    parser = argparse.ArgumentParser(description="주간 분석 백필")
    parser.add_argument("--start",   required=True, help="시작 날짜 (YYYY-MM-DD)")
    parser.add_argument("--end",     required=True, help="종료 날짜 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="실제 쓰기 없이 대상 목록만 출력")
    args = parser.parse_args()

    mondays = get_mondays(args.start, args.end)
    if not mondays:
        print("지정 기간에 월요일이 없습니다. 종료.")
        sys.exit(0)

    print(f"\n[주간 백필]")
    print(f"  기간: {args.start} ~ {args.end}")
    print(f"  주 수: {len(mondays)}주")
    print(f"  분석 주 시작일: {', '.join(mondays)}")

    if args.dry_run:
        print("\n[dry-run] 대상 목록만 출력합니다.")
        for m in mondays:
            # 주 종료일 (일요일)
            end_d = date.fromisoformat(m) + timedelta(days=6)
            print(f"  {m} ~ {end_d.isoformat()}")
        return

    run_id = f"weekly-backfill-{args.start}-{args.end}-{uuid.uuid4().hex[:6]}"

    from analyzer.weekly import run as weekly_run
    from sheets.writer import upsert_weekly_galleries, append_weekly_overall

    succeeded = 0
    failed = 0

    for week_start in mondays:
        print(f"\n── {week_start} ──", flush=True)
        try:
            result = weekly_run(week_start=week_start, verbose=True)
            if not result.get("galleries"):
                print(f"  데이터 없음 — 건너뜀", flush=True)
                continue

            wk_start  = result["week_start"]
            wk_end    = result["week_end"]
            galleries = result["galleries"]

            upsert_weekly_galleries(galleries, week_start=wk_start, week_end=wk_end, run_id=run_id)
            append_weekly_overall(result["overall_summary"], week_start=wk_start, week_end=wk_end, run_id=run_id)
            print(f"  ✓ {wk_start} ~ {wk_end}  ({len(galleries)}개 갤러리)", flush=True)
            succeeded += 1
        except Exception as e:
            print(f"  ✗ 오류: {e}", flush=True)
            failed += 1

        time.sleep(5)

    print(f"\n✅ 완료: {succeeded}주 처리 / 실패 {failed}주")


if __name__ == "__main__":
    main()
