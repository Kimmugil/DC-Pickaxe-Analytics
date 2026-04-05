#!/usr/bin/env python3
"""
DC-Pickaxe Analytics — 분석 봇 진입점

매일 00:00 KST GitHub Actions cron에서 자동 실행됩니다.

사용법:
  python run_analysis.py                    # 오늘 신규 분석
  python run_analysis.py --rerun A1B2C3D4   # 특정 회차 재분석
  python run_analysis.py --init-headers     # 시트 헤더 초기화 (최초 1회)
  python run_analysis.py --no-notion        # Notion 발행 없이 분석만
"""
import os
import sys
import uuid
import argparse
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from sheets.reader import get_gallery_list, get_gallery_posts, get_posts_by_run_id
from sheets.writer import (
    save_analysis_result,
    save_analysis_posts,
    save_cross_gallery_summary,
    ensure_sheet_headers,
)
from analyzer.data_fetcher import select_posts_for_analysis
from analyzer.stats_analyzer import analyze_post_trends, analyze_activity
from analyzer.keyword_analyzer import extract_keywords
from analyzer.popular_posts import get_top_posts
from analyzer.ai_summarizer import summarize_gallery, summarize_all_galleries
from analyzer.gaming_analyzer import analyze_gaming_signals
from notion.publisher import publish_daily_report


def generate_run_id() -> str:
    """8자리 대문자 16진수 고유 ID를 생성합니다. (예: A1B2C3D4)"""
    return uuid.uuid4().hex[:8].upper()


def analyze_one_gallery(
    gallery: dict,
    run_id: str,
    date_str: str,
    rerun_posts_df=None,
) -> dict | None:
    """
    갤러리 하나를 분석하고 결과를 반환합니다.

    Args:
        gallery: 마스터 시트에서 읽은 갤러리 정보 dict
        run_id: 이번 분석 회차 ID
        date_str: 분석 기준 날짜 (YYYY-MM-DD)
        rerun_posts_df: 재분석 시 사용할 기존 게시글 DataFrame (None이면 신규 분석)

    Returns:
        분석 결과 dict 또는 None (스킵)
    """
    gallery_name = gallery.get('갤러리명') or gallery.get('gallery_name', '?')
    gallery_id   = gallery.get('갤러리ID') or gallery.get('gallery_id', '')
    sheet_url    = gallery.get('저장시트 URL') or gallery.get('저장시트URL') or gallery.get('sheet_url', '')

    print(f"\n  ▶ [{gallery_name}]")

    # ── 게시글 로딩 ──
    if rerun_posts_df is not None and not rerun_posts_df.empty:
        posts_df = rerun_posts_df.rename(columns={
            '글번호': '글번호', '제목': '제목', '본문요약': '본문',
            '작성자': '작성자', '게시일시': '날짜',
        })
        # 날짜 컬럼 복원
        if '날짜' in posts_df.columns:
            import pandas as pd
            posts_df['날짜'] = pd.to_datetime(posts_df['날짜'], errors='coerce')
        selected_df = posts_df.copy()
        selected_df['선택이유'] = '재분석(기존회차)'
        print(f"     재분석 모드: {len(selected_df)}개 게시글 사용")
    else:
        if not sheet_url:
            print(f"     시트 URL 없음, 스킵")
            return None
        posts_df = get_gallery_posts(sheet_url)
        if posts_df.empty:
            print(f"     데이터 없음, 스킵")
            return None
        selected_df = select_posts_for_analysis(posts_df, analysis_date=date_str)
        print(f"     전체 {len(posts_df)}개 중 {len(selected_df)}개 선정")

        # 분석 대상 게시글 기록 (이 회차에 어떤 게시글을 썼는지 추적 가능)
        save_analysis_posts(
            posts=selected_df.to_dict('records'),
            run_id=run_id,
            date=date_str,
            gallery_id=gallery_id,
            gallery_name=gallery_name,
        )

    # ── 분석 실행 ──
    print(f"     통계 분석 중...")
    trends  = analyze_post_trends(posts_df if rerun_posts_df is None else selected_df, date_str)
    activity = analyze_activity(posts_df if rerun_posts_df is None else selected_df, date_str)
    keywords = extract_keywords(selected_df)
    top5     = get_top_posts(selected_df)
    signals  = analyze_gaming_signals(selected_df)

    print(f"     AI 요약 생성 중 (Gemini)...")
    stats = {**trends, **activity}
    ai_summary = summarize_gallery(selected_df, gallery_name, stats, keywords, signals)

    result = {
        'run_id':          run_id,
        'date':            date_str,
        'gallery_id':      gallery_id,
        'gallery_name':    gallery_name,
        'total_posts':     trends.get('total_posts', 0),
        'new_posts_today': trends.get('new_posts_today', 0),
        'new_posts_7d':    trends.get('new_posts_7d', 0),
        'top5_posts':      top5,
        'top_keywords':    keywords,
        'hourly_dist':     activity.get('hourly_dist', {}),
        'game_signals':    signals,
        'ai_summary':      ai_summary,
    }

    save_analysis_result(result)
    print(f"     완료 ✓")
    return result


def main():
    parser = argparse.ArgumentParser(description='DC-Pickaxe Analytics 분석 봇')
    parser.add_argument('--rerun',         type=str,            help='재분석할 run_id (8자리)')
    parser.add_argument('--init-headers',  action='store_true', help='시트 헤더 초기화 (최초 1회)')
    parser.add_argument('--no-notion',     action='store_true', help='Notion 발행 건너뜀')
    parser.add_argument('--analysis-date', type=str,            help='분석 기준일 YYYY-MM-DD (미입력 시 어제)')
    args = parser.parse_args()

    # 헤더 초기화 모드
    if args.init_headers:
        print("=== 시트 헤더 초기화 ===")
        ensure_sheet_headers()
        print("완료!")
        return

    if args.analysis_date:
        date_str = args.analysis_date
    else:
        date_str = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    run_id = args.rerun if args.rerun else generate_run_id()

    if args.rerun:
        print(f"=== 재분석 시작 ===")
        print(f"  run_id : {run_id}")
        print(f"  날짜   : {date_str}")
    else:
        print(f"=== 신규 분석 시작 ===")
        print(f"  run_id : {run_id}")
        print(f"  날짜   : {date_str}")

    # 갤러리 목록 로드
    print("\n갤러리 목록 로딩 중...")
    galleries = get_gallery_list()
    print(f"{len(galleries)}개 갤러리 발견")

    all_results = []

    for gallery in galleries:
        try:
            rerun_df = None
            if args.rerun:
                all_rerun = get_posts_by_run_id(run_id)
                gid = gallery.get('갤러리ID') or gallery.get('gallery_id', '')
                rerun_df = all_rerun[all_rerun['gallery_id'] == gid] if not all_rerun.empty else None

            result = analyze_one_gallery(gallery, run_id, date_str, rerun_posts_df=rerun_df)
            if result:
                all_results.append(result)

        except Exception as e:
            name = gallery.get('갤러리명', '?')
            print(f"  [{name}] 오류: {e}")
            import traceback
            traceback.print_exc()
            continue

    if not all_results:
        print("\n분석된 갤러리가 없습니다.")
        sys.exit(1)

    # 크로스 갤러리 종합 요약
    print("\n크로스 갤러리 종합 요약 생성 중 (Gemini)...")
    cross_summary = summarize_all_galleries(all_results)
    save_cross_gallery_summary(run_id, date_str, cross_summary)

    # Notion 발행
    if not args.no_notion and os.environ.get('NOTION_TOKEN'):
        print("Notion 보고서 발행 중...")
        try:
            url = publish_daily_report(date_str, all_results, cross_summary)
            print(f"Notion 발행 완료: {url}")
        except Exception as e:
            print(f"Notion 발행 실패 (분석 결과는 저장됨): {e}")
    else:
        print("Notion 발행 건너뜀")

    print(f"\n{'='*40}")
    print(f"분석 완료!")
    print(f"  run_id : {run_id}  ← 재분석 시 사용")
    print(f"  갤러리 : {len(all_results)}개")
    print(f"  날짜   : {date_str}")
    print(f"{'='*40}")


if __name__ == '__main__':
    main()
