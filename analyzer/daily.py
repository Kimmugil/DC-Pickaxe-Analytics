"""
일간 이슈 분석

실행 흐름:
  1. 마스터시트에서 갤러리 목록 조회
  2. 갤러리별 target_date 게시글 전량 수집
  3. 최근 7일 평균 대비 이슈 점수 계산
  4. 이슈 감지(score >= 3) 갤러리만 Gemini AI 요약 생성
  5. 전체 결과 반환 (has_issue=0 포함)
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

import pandas as pd

from sheets import reader
from analyzer import keywords as kw_mod
from analyzer.ai_summary import summarize_daily_issue


ISSUE_THRESHOLD = 5   # 이슈 판정 최소 점수 (구: 3 → 신: 5)


def _engagement(post: dict) -> float:
    comments = int(post.get("댓글수", 0) or 0)
    likes    = int(post.get("추천수", 0) or 0)
    views    = float(post.get("조회수", 0) or 0)
    return comments * 3 + likes * 2 + views * 0.05


def _issue_posts(posts: list[dict], n: int = 5) -> list[dict]:
    """댓글 수 기준 정렬 — 가장 많이 논의된 = 이슈를 일으킨 게시글."""
    scored = sorted(posts, key=lambda p: int(p.get("댓글수", 0) or 0), reverse=True)
    result = []
    for p in scored[:n]:
        result.append({
            "제목":   str(p.get("제목", "")),
            "링크":   str(p.get("링크", "")),
            "날짜":   str(p.get("날짜", ""))[:10],
            "댓글수": int(p.get("댓글수", 0) or 0),
            "추천수": int(p.get("추천수", 0) or 0),
            "조회수": int(p.get("조회수", 0) or 0),
        })
    return result


def _calc_issue_score(
    posts_today: list[dict],
    count_today: int,
    avg_7d: float,
) -> int:
    """
    이슈 점수 산출 (최대 10점, 임계값 ISSUE_THRESHOLD 이상이면 이슈 판정)

    ① 게시량 급증 (비율 × 절대 증분 복합 조건)
       - 비율만 높아도 절대 증가폭이 작으면 점수 없음
       - 예: 평균 2건 → 오늘 5건 = 2.5배지만 +3건이므로 점수 없음
    ② 단일 게시글 화제성 (댓글·추천 수)
    ③ 바이럴 확산 (화제 게시글 복수 존재 여부)
    """
    score = 0

    # ① 게시량 급증 (비율 + 절대 증분 모두 만족)
    if avg_7d > 0:
        ratio = count_today / avg_7d
        delta = count_today - avg_7d
        if ratio >= 3.0 and delta >= 20:
            score += 4
        elif ratio >= 2.5 and delta >= 10:
            score += 3
        elif ratio >= 2.0 and delta >= 5:
            score += 2
        elif ratio >= 1.5 and delta >= 3:
            score += 1

    # ② 단일 게시글 화제성
    if posts_today:
        top = sorted(posts_today, key=_engagement, reverse=True)
        t1_comments = int(top[0].get("댓글수", 0) or 0)
        t1_likes    = int(top[0].get("추천수", 0) or 0)
        if t1_comments >= 50:
            score += 3
        elif t1_comments >= 30:
            score += 2
        elif t1_comments >= 15:
            score += 1
        if t1_likes >= 20:
            score += 2
        elif t1_likes >= 10:
            score += 1

    # ③ 바이럴 확산 (댓글 10개 이상 게시글 복수 존재)
    hot_posts = sum(1 for p in posts_today if int(p.get("댓글수", 0) or 0) >= 10)
    if hot_posts >= 5:
        score += 2
    elif hot_posts >= 3:
        score += 1

    return min(score, 10)


def _analyze_gallery(
    gallery: dict,
    target_date: str,
    verbose: bool = False,
) -> dict:
    sheet_url    = gallery["sheet_url"]
    gallery_id   = gallery["gallery_id"]
    gallery_name = gallery["gallery_name"]

    df_today    = reader.get_posts_by_date(sheet_url, target_date)
    posts_today = df_today.to_dict("records") if not df_today.empty else []
    count_today = len(posts_today)

    daily_counts = reader.get_daily_counts(sheet_url, target_date, lookback_days=7)
    past_counts  = [v for k, v in daily_counts.items() if k != target_date]
    avg_7d       = sum(past_counts) / len(past_counts) if past_counts else 0.0

    issue_score = _calc_issue_score(posts_today, count_today, avg_7d)
    has_issue   = issue_score >= ISSUE_THRESHOLD
    keywords    = kw_mod.extract(posts_today, top_n=10)
    top5        = _issue_posts(posts_today, n=5)

    if verbose:
        flag = "이슈" if has_issue else "정상"
        print(f"  {gallery_name}: {count_today}건 (평균 {avg_7d:.0f}) 점수:{issue_score} {flag}", flush=True)

    return {
        "gallery_id":   gallery_id,
        "gallery_name": gallery_name,
        "posts_total":  count_today,
        "avg_7d":       round(avg_7d, 1),
        "issue_score":  issue_score,
        "has_issue":    has_issue,
        "keywords":     keywords,
        "top_posts":    top5,
        "ai_summary":   "",
    }


def run(target_date: str | None = None, verbose: bool = True) -> list[dict]:
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"\n[일간 분석] 대상 날짜: {target_date}", flush=True)

    galleries = reader.get_gallery_list()
    if not galleries:
        print("  갤러리 목록 없음", flush=True)
        return []

    results = []
    for i, g in enumerate(galleries):
        if i > 0:
            time.sleep(2)  # 갤러리 간 2초 딜레이 (429 방지)
        try:
            result = _analyze_gallery(g, target_date, verbose=verbose)
            results.append(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  실패: {g['gallery_name']} - {e}", flush=True)
            results.append({
                "gallery_id":   g["gallery_id"],
                "gallery_name": g["gallery_name"],
                "posts_total":  0,
                "avg_7d":       0.0,
                "issue_score":  0,
                "has_issue":    False,
                "keywords":     [],
                "top_posts":    [],
                "ai_summary":   "",
            })

    issue_results = [r for r in results if r["has_issue"]]
    if issue_results:
        print(f"\n[AI 요약] 이슈 갤러리 {len(issue_results)}개...", flush=True)
        for r in issue_results:
            try:
                r["ai_summary"] = summarize_daily_issue(
                    gallery_name=r["gallery_name"],
                    top_posts=r["top_posts"],
                    keywords=r["keywords"],
                    issue_score=r["issue_score"],
                    count_today=r["posts_total"],
                    avg_7d=r["avg_7d"],
                )
                if verbose:
                    print(f"  완료: {r['gallery_name']}", flush=True)
            except Exception as e:
                r["ai_summary"] = ""
                print(f"  AI 요약 실패: {r['gallery_name']} - {e}", flush=True)
    elif verbose:
        print("  이슈 갤러리 없음 - AI 요약 생략", flush=True)

    return results
