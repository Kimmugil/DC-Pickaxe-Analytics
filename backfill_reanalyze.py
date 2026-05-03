"""
전체 재분석 백필 스크립트 (v2)

기존 daily_issues 데이터를 새 AI 분석 구조(본문 샘플 + 구조화 출력)로 재처리합니다.
(date, gallery_id) 기준 upsert — 기존 행 덮어쓰기, 없으면 신규 추가.

사용법:
  python backfill_reanalyze.py --start 2025-04-01 --end 2025-04-30
  python backfill_reanalyze.py --start 2025-04-01 --end 2025-04-30 --dry-run
  python backfill_reanalyze.py --start 2025-04-01 --end 2025-04-30 --gallery maple-story-mobile
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

from analyzer import daily as daily_mod
from sheets import reader, writer


def date_range(start: str, end: str) -> list[str]:
    d0 = date.fromisoformat(start)
    d1 = date.fromisoformat(end)
    days = (d1 - d0).days + 1
    return [(d0 + timedelta(days=i)).isoformat() for i in range(days)]


def main() -> None:
    parser = argparse.ArgumentParser(description="일간 이슈 전체 재분석 백필")
    parser.add_argument("--start",   required=True, help="시작 날짜 (YYYY-MM-DD)")
    parser.add_argument("--end",     required=True, help="종료 날짜 (YYYY-MM-DD)")
    parser.add_argument("--gallery", default="",    help="특정 gallery_id만 처리 (생략 시 전체)")
    parser.add_argument("--dry-run", action="store_true", help="실제 쓰기 없이 대상 목록만 출력")
    args = parser.parse_args()

    dates = date_range(args.start, args.end)
    galleries = reader.get_gallery_list()

    if not galleries:
        print("갤러리 목록 없음. 종료.")
        sys.exit(1)

    if args.gallery:
        galleries = [g for g in galleries if g["gallery_id"] == args.gallery]
        if not galleries:
            print(f"gallery_id '{args.gallery}'를 찾을 수 없습니다.")
            sys.exit(1)

    total = len(dates) * len(galleries)
    print(f"\n[재분석 백필]")
    print(f"  기간: {args.start} ~ {args.end}  ({len(dates)}일)")
    print(f"  갤러리: {len(galleries)}개")
    print(f"  총 작업: {total}건")

    if args.dry_run:
        print("\n[dry-run] 대상 목록만 출력합니다.")
        for d in dates:
            for g in galleries:
                print(f"  {d}  {g['gallery_name']}")
        return

    import uuid
    run_id = f"backfill-{args.start}-{args.end}-{uuid.uuid4().hex[:6]}"

    processed = 0
    failed    = 0

    for target_date in dates:
        print(f"\n── {target_date} ──", flush=True)
        results = daily_mod.run(target_date=target_date, verbose=True)

        if args.gallery:
            results = [r for r in results if r["gallery_id"] == args.gallery]

        if results:
            try:
                writer.upsert_daily_issues(results, target_date, run_id)
                processed += len(results)
            except Exception as e:
                print(f"  시트 쓰기 실패: {e}", flush=True)
                failed += len(results)

        # 날짜 간 딜레이 (API rate limit 방지)
        time.sleep(5)

    print(f"\n✅ 완료: {processed}행 upsert / 실패 {failed}행")


if __name__ == "__main__":
    main()
