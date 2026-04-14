"""
주간 분석 실행 스크립트

사용법:
  python run_weekly.py                         # 지난 주 분석
  python run_weekly.py --week-start 2026-04-07 # 특정 주 분석 (월요일 날짜)
"""

import argparse
import sys
import uuid
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()


def main() -> None:
    parser = argparse.ArgumentParser(description="DC-Pickaxe 주간 분석")
    parser.add_argument("--week-start", help="분석 주 시작일 (YYYY-MM-DD, 월요일). 미입력시 지난 주.")
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6].upper()

    print("=== 주간 분석 ===")
    if args.week_start:
        print(f"주 시작일: {args.week_start}  |  run_id: {run_id}")
    else:
        print(f"지난 주 자동 계산  |  run_id: {run_id}")

    from analyzer.weekly import run as weekly_run
    result = weekly_run(week_start=args.week_start, verbose=True)

    if not result["galleries"]:
        print("\n⚠️  분석 결과 없음 — 종료")
        sys.exit(0)

    week_start = result["week_start"]
    week_end   = result["week_end"]
    galleries  = result["galleries"]

    print(f"\n분석 완료: {len(galleries)}개 갤러리 ({week_start} ~ {week_end})")

    from sheets.writer import append_weekly_galleries, append_weekly_overall
    append_weekly_galleries(galleries, week_start=week_start, week_end=week_end, run_id=run_id)
    print(f"시트 적재 완료 → weekly_galleries ({len(galleries)}행)")

    append_weekly_overall(result["overall_summary"], week_start=week_start, week_end=week_end, run_id=run_id)
    print("시트 적재 완료 → weekly_overall (1행)")
    print(f"✅ 주간 리포트 발행: {week_start} ~ {week_end}")


if __name__ == "__main__":
    main()
