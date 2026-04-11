#!/usr/bin/env python3
"""
DC-Pickaxe Analytics — 일간 분석 봇 진입점

매일 00:00 UTC (KST 09:00) GitHub Actions cron에서 자동 실행됩니다.

사용법:
  python run_analysis.py                      # 신규 분석 (어제 기준)
  python run_analysis.py --rerun A1B2C3D4     # 특정 회차 재분석
  python run_analysis.py --init-headers       # 시트 헤더 초기화 (최초 1회)
  python run_analysis.py --analysis-date DATE # 특정 날짜 기준 분석
"""
import os
import sys
import uuid
import json
import argparse
from datetime import datetime, timedelta

from dotenv import load_dotenv
load_dotenv()

from sheets.reader import get_gallery_list, get_gallery_posts, get_gallery_stats, get_posts_by_run_id
from sheets.writer import (
    save_analysis_result,
    save_analysis_posts,
    ensure_sheet_headers,
)
from analyzer.data_fetcher import select_posts_for_analysis
from analyzer.stats_analyzer import analyze_post_trends, analyze_activity
from analyzer.keyword_analyzer import extract_keywords
from analyzer.popular_posts import get_top_posts
from analyzer.ai_summarizer import summarize_gallery_issue
from analyzer.gaming_analyzer import analyze_gaming_signals


def generate_run_id() -> str:
    return uuid.uuid4().hex[:8].upper()


def calculate_issue_score(result: dict) -> tuple[bool, int]:
    """
    갤러리 이슈 발생 여부를 판단합니다.
    Returns: (has_issue, issue_score)
    """
    score = 0

    # game_signals 기반 점수
    signals = result.get('game_signals', {})
    if isinstance(signals, str):
        try:
            signals = json.loads(signals)
        except Exception:
            signals = {}
    for sig_data in signals.values():
        if isinstance(sig_data, dict):
            ratio = sig_data.get('ratio', 0)
            if ratio >= 10:
                score += 3
            elif ratio >= 5:
                score += 1

    # TOP 게시글 참여도 기반 점수
    top5 = result.get('top5_posts', [])
    if isinstance(top5, str):
        try:
            top5 = json.loads(top5)
        except Exception:
            top5 = []
    if top5:
        tp = top5[0]
        if tp.get('댓글수', 0) > 30:
            score += 2
        elif tp.get('댓글수', 0) > 15:
            score += 1
        if tp.get('추천수', 0) > 15:
            score += 2
        elif tp.get('추천수', 0) > 7:
            score += 1

    # 24h 신규 게시글이 평소보다 급증하면 이슈 신호
    new_today = int(result.get('new_posts_today', 0))
    new_7d    = int(result.get('new_posts_7d', 0))
    daily_avg = new_7d / 7 if new_7d else 0
    if daily_avg > 0 and new_today > daily_avg * 2:
        score += 2

    has_issue = score >= 3
    return has_issue, score


def analyze_one_gallery(
    gallery: dict,
    run_id: str,
    date_str: str,
    rerun_posts_df=None,
) -> dict | None:
    import pandas as pd

    gallery_name = gallery.get('갤러리명') or gallery.get('gallery_name', '?')
    gallery_id   = gallery.get('갤러리ID') or gallery.get('gallery_id', '')
    sheet_url    = (gallery.get('저장시트 URL') or gallery.get('저장시트URL')
                    or gallery.get('sheet_url', ''))

    print(f"\n  ▶ [{gallery_name}]")

    if rerun_posts_df is not None and not rerun_posts_df.empty:
        posts_df = rerun_posts_df.rename(columns={'게시일시': '날짜', '본문요약': '본문'})
        if '날짜' in posts_df.columns:
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
        save_analysis_posts(
            posts=selected_df.to_dict('records'),
            run_id=run_id, date=date_str,
            gallery_id=gallery_id, gallery_name=gallery_name,
        )

    print(f"     통계 분석 중...")
    src_df   = posts_df if rerun_posts_df is None else selected_df
    trends   = analyze_post_trends(src_df, date_str)
    activity = analyze_activity(src_df, date_str)
    keywords = extract_keywords(selected_df)
    top5     = get_top_posts(selected_df)
    signals  = analyze_gaming_signals(selected_df)

    # stats 시트에서 정확한 게시글 수 가져오기
    new_posts_today = trends.get('new_posts_today', 0)
    new_posts_7d    = trends.get('new_posts_7d', 0)
    total_posts     = trends.get('total_posts', 0)
    if sheet_url and rerun_posts_df is None:
        try:
            from datetime import timedelta as _td
            stats_data = get_gallery_stats(sheet_url)
            if stats_data:
                new_posts_today = stats_data.get(date_str, new_posts_today)
                date_dt = datetime.strptime(date_str, '%Y-%m-%d')
                new_posts_7d = sum(
                    stats_data.get(
                        (date_dt - _td(days=i)).strftime('%Y-%m-%d'), 0
                    )
                    for i in range(7)
                )
                total_posts = sum(stats_data.values())
        except Exception as e:
            print(f"     stats 시트 로딩 실패 (기존 방식 사용): {e}")

    stats = {**trends, **activity,
             'new_posts_today': new_posts_today,
             'new_posts_7d':    new_posts_7d}

    result = {
        'run_id':          run_id,
        'date':            date_str,
        'gallery_id':      gallery_id,
        'gallery_name':    gallery_name,
        'total_posts':     total_posts,
        'new_posts_today': new_posts_today,
        'new_posts_7d':    new_posts_7d,
        'top5_posts':      top5,
        'top_keywords':    keywords,
        'hourly_dist':     activity.get('hourly_dist', {}),
        'game_signals':    signals,
        'ai_summary':      '',    # 이슈 판별 후 조건부 생성
    }

    # 이슈 판별
    has_issue, issue_score = calculate_issue_score(result)
    result['has_issue']   = 1 if has_issue else 0
    result['issue_score'] = issue_score

    # 이슈가 있는 갤러리만 AI 요약 생성 (비용 절감)
    if has_issue:
        print(f"     AI 이슈 요약 생성 중 (Gemini)... [이슈점수: {issue_score}]")
        result['ai_summary'] = summarize_gallery_issue(
            selected_df, gallery_name, stats, keywords[:5], signals, top5[:5]
        )
    else:
        print(f"     이슈 없음 (점수 {issue_score}) - AI 요약 생략")
        result['ai_summary'] = ''

    save_analysis_result(result)
    print(f"     완료 ✓ {'[이슈]' if has_issue else ''}")
    return result


def main():
    parser = argparse.ArgumentParser(description='DC-Pickaxe Analytics 일간 분석 봇')
    parser.add_argument('--rerun',         type=str,            help='재분석할 run_id (8자리)')
    parser.add_argument('--init-headers',  action='store_true', help='시트 헤더 초기화 (최초 1회)')
    parser.add_argument('--analysis-date', type=str,            help='분석 기준일 YYYY-MM-DD (미입력 시 어제)')
    args = parser.parse_args()

    if args.init_headers:
        print("=== 시트 헤더 초기화 ===")
        ensure_sheet_headers()
        print("완료!")
        return

    date_str = (
        args.analysis_date if args.analysis_date
        else (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    )
    run_id = args.rerun if args.rerun else generate_run_id()

    print(f"=== {'재분석' if args.rerun else '신규 분석'} 시작 ===")
    print(f"  run_id : {run_id}")
    print(f"  날짜   : {date_str}")

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
                rerun_df = (all_rerun[all_rerun['gallery_id'] == gid]
                            if not all_rerun.empty else None)

            result = analyze_one_gallery(gallery, run_id, date_str, rerun_posts_df=rerun_df)
            if result:
                all_results.append(result)
        except Exception as e:
            name = gallery.get('갤러리명', '?')
            print(f"  [{name}] 오류: {e}")
            import traceback; traceback.print_exc()

    if not all_results:
        print("\n분석된 갤러리가 없습니다.")
        sys.exit(1)

    has_any_issue = any(r.get('has_issue', 0) for r in all_results)
    print(f"\n이슈 발생 갤러리: {sum(r.get('has_issue',0) for r in all_results)}개 "
          f"/ 전체 {len(all_results)}개")

    print(f"\n{'='*40}")
    print(f"분석 완료! run_id: {run_id}")
    print(f"{'='*40}")


if __name__ == '__main__':
    main()
