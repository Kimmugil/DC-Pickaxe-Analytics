"""
월간 분석 실행 스크립트

사용법:
  python run_monthly.py                      # 직전 월
  python run_monthly.py --month 2026-04      # 특정 월
  python run_monthly.py --dry-run            # 시트 쓰기 없이 미리보기
"""

import argparse
import sys
from datetime import datetime

from analyzer import monthly as monthly_mod
from sheets import writer


def main():
    parser = argparse.ArgumentParser(description="월간 분석 실행")
    parser.add_argument("--month",   default=None, help="분석 월 (YYYY-MM). 미지정 시 직전 월")
    parser.add_argument("--dry-run", action="store_true", help="시트 쓰기 없이 대상만 출력")
    args = parser.parse_args()

    result = monthly_mod.run(month=args.month, verbose=True, dry_run=args.dry_run)

    if args.dry_run:
        print("\n[DRY-RUN] 결과 미리보기:")
        for r in result["galleries"]:
            print(f"  {r['gallery_name']}: 이슈 {r['issue_days']}일, 최고 {r['max_issue_score']}점, top_cause={r['top_cause']}")
        print(f"\n  전체: {len(result['galleries'])}개 갤러리")
        sys.exit(0)

    if not result["galleries"]:
        print("분석 결과 없음. 종료합니다.")
        sys.exit(0)

    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    month  = result["month"]

    print(f"\n[시트 저장] monthly_issues 업로드 중...")
    writer.upsert_monthly_issues(result["galleries"], month, run_id)

    print(f"[시트 저장] monthly_overall 업로드 중...")
    writer.upsert_monthly_overall(result["overall_summary"], month, run_id)

    print(f"\n✅ 월간 분석 완료: {month} ({len(result['galleries'])}개 갤러리)")


if __name__ == "__main__":
    main()
