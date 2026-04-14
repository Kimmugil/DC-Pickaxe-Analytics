"""
일간 이슈 분석 실행 스크립트

사용법:
  python run_daily.py                      # 어제 날짜 분석
  python run_daily.py --date 2026-04-13    # 특정 날짜 분석
  python run_daily.py --setup              # Analytics 시트 초기화 (최초 1회)
"""

import argparse
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

import uuid


def main() -> None:
    parser = argparse.ArgumentParser(description="DC-Pickaxe 일간 이슈 분석")
    parser.add_argument("--date",  help="분석 날짜 (YYYY-MM-DD). 미입력시 어제.")
    parser.add_argument("--setup", action="store_true", help="Analytics 시트 초기화")
    args = parser.parse_args()

    if args.setup:
        print("=== Analytics 시트 초기화 ===")
        from sheets.writer import setup_sheets
        setup_sheets()
        print("완료")
        return

    target_date = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    run_id      = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6].upper()

    print(f"=== 일간 이슈 분석 ===")
    print(f"날짜: {target_date}  |  run_id: {run_id}")

    from analyzer.daily import run as daily_run
    results = daily_run(target_date=target_date, verbose=True)

    if not results:
        print("\n⚠️  분석 결과 없음 — 종료")
        sys.exit(0)

    issue_count = sum(1 for r in results if r.get("has_issue"))
    print(f"\n분석 완료: {len(results)}개 갤러리 / 이슈 {issue_count}개")

    from sheets.writer import append_daily_issues
    append_daily_issues(results, date=target_date, run_id=run_id)
    print(f"시트 적재 완료 → daily_issues ({len(results)}행)")

    if issue_count == 0:
        print("이슈 없음 — 일간 리포트 미발행")
    else:
        print(f"✅ 이슈 감지: {issue_count}개 갤러리 — 일간 이슈 리포트 발행")


if __name__ == "__main__":
    main()
