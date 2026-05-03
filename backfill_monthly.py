"""
월간 분석 백필 스크립트

지정 기간의 모든 달을 순서대로 분석해 monthly_issues / monthly_overall 시트에 적재합니다.

사용법:
  python backfill_monthly.py --start 2026-01 --end 2026-04
  python backfill_monthly.py --start 2026-01 --end 2026-04 --dry-run
"""

import argparse
import sys
from datetime import date, datetime

from analyzer import monthly as monthly_mod
from sheets import writer


def months_in_range(start: str, end: str) -> list[str]:
    """start ~ end 사이의 모든 YYYY-MM 목록."""
    sy, sm = map(int, start.split("-"))
    ey, em = map(int, end.split("-"))
    result = []
    y, m = sy, sm
    while (y, m) <= (ey, em):
        result.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return result


def main():
    parser = argparse.ArgumentParser(description="월간 분석 백필")
    parser.add_argument("--start",   required=True, help="시작 월 (YYYY-MM)")
    parser.add_argument("--end",     required=True, help="종료 월 (YYYY-MM)")
    parser.add_argument("--dry-run", action="store_true", help="시트 쓰기 없이 대상만 출력")
    args = parser.parse_args()

    months = months_in_range(args.start, args.end)
    print(f"백필 대상 월: {months}")

    if args.dry_run:
        print("[DRY-RUN] 실제 쓰기 없이 실행합니다.\n")

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    for month in months:
        result = monthly_mod.run(month=month, verbose=True, dry_run=args.dry_run)

        if args.dry_run:
            print(f"  → {month}: {len(result['galleries'])}개 갤러리 (dry-run)\n")
            continue

        if not result["galleries"]:
            print(f"  → {month}: 데이터 없음, 스킵\n")
            continue

        writer.upsert_monthly_issues(result["galleries"], month, run_id)
        writer.upsert_monthly_overall(result["overall_summary"], month, run_id)
        print(f"  → {month}: 완료 ({len(result['galleries'])}개 갤러리)\n")

    print("백필 완료!")


if __name__ == "__main__":
    main()
