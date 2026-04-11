#!/usr/bin/env python3
"""
DC-Pickaxe Analytics — 주간 분석 봇 진입점

매주 월요일 00:00 UTC (KST 09:00) GitHub Actions cron에서 자동 실행됩니다.
대상 기간: 지난 주 월요일~일요일

사용법:
  python run_weekly.py                           # 지난 주 기준
  python run_weekly.py --week-start 2026-03-30   # 특정 주 기준
"""
import os
import sys
import uuid
import argparse
from datetime import datetime, date, timedelta

from dotenv import load_dotenv
load_dotenv()

from sheets.reader import get_gallery_list
from sheets.writer import save_weekly_gallery_result, save_weekly_summary
from analyzer.weekly_analyzer import analyze_gallery_weekly
from analyzer.ai_summarizer import summarize_weekly_gallery, summarize_weekly_overview


def generate_run_id() -> str:
    return uuid.uuid4().hex[:8].upper()


def get_last_week_range() -> tuple[date, date]:
    """지난 주 월요일~일요일 범위를 반환합니다."""
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(weeks=1)
    last_sunday = last_monday + timedelta(days=6)
    return last_monday, last_sunday


def main():
    parser = argparse.ArgumentParser(description='DC-Pickaxe Analytics 주간 분석 봇')
    parser.add_argument(
        '--week-start', type=str,
        help='분석 시작일 YYYY-MM-DD (월요일, 미입력 시 지난 주)',
    )
    args = parser.parse_args()

    if args.week_start:
        week_start = date.fromisoformat(args.week_start)
        week_end   = week_start + timedelta(days=6)
    else:
        week_start, week_end = get_last_week_range()

    week_start_str = week_start.strftime('%Y-%m-%d')
    week_end_str   = week_end.strftime('%Y-%m-%d')
    run_id         = generate_run_id()

    print(f"=== 주간 분석 시작 ===")
    print(f"  run_id : {run_id}")
    print(f"  기간   : {week_start_str} ~ {week_end_str}")

    print("\n갤러리 목록 로딩 중...")
    galleries = get_gallery_list()
    print(f"{len(galleries)}개 갤러리 발견")

    gallery_results = []

    for gallery in galleries:
        name = gallery.get('갤러리명') or gallery.get('gallery_name', '?')
        print(f"\n  ▶ [{name}]")
        try:
            result = analyze_gallery_weekly(gallery, week_start, week_end)
            if result is None:
                print(f"     시트 URL 없음, 스킵")
                continue

            total = result.get('total_posts_week', 0)
            if total >= 5:
                print(f"     AI 주간 갤러리 요약 생성 중... ({total}건)")
                ai_summary = summarize_weekly_gallery(
                    gallery_name=result['gallery_name'],
                    week_start=week_start_str,
                    week_end=week_end_str,
                    total_posts=total,
                    keywords=result.get('top_keywords', []),
                    top5_posts=result.get('top5_posts', []),
                )
            else:
                print(f"     게시글 부족 ({total}건) - AI 요약 생략")
                ai_summary = f"> 주간 게시글 부족 ({total}건)"

            result['ai_gallery_weekly'] = ai_summary
            result['run_id']     = run_id
            result['week_start'] = week_start_str
            result['week_end']   = week_end_str

            save_weekly_gallery_result(result)
            print(f"     저장 완료 ({total}건)")
            gallery_results.append(result)

        except Exception as e:
            print(f"     오류: {e}")
            import traceback; traceback.print_exc()

    if not gallery_results:
        print("\n분석된 갤러리가 없습니다.")
        sys.exit(1)

    print(f"\n총 {len(gallery_results)}개 갤러리 주간 분석 완료")
    print("\n종합 주간 요약 생성 중 (Gemini)...")
    try:
        overview = summarize_weekly_overview(gallery_results, week_start_str, week_end_str)
        save_weekly_summary(run_id, week_start_str, week_end_str, overview)
        print("종합 요약 저장 완료")
    except Exception as e:
        print(f"종합 요약 오류: {e}")
        import traceback; traceback.print_exc()

    print(f"\n{'='*40}")
    print(f"주간 분석 완료! run_id: {run_id}")
    print(f"{'='*40}")


if __name__ == '__main__':
    main()
