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

from datetime import datetime, timedelta

import pandas as pd

from sheets import reader
from analyzer import keywords as kw_mod
from analyzer.ai_summary import summarize_daily_issue


# ── 이슈 점수 기준 ────────────────────────────────────────────────────
ISSUE_THRESHOLD = 3   # 이상 → 이슈 판정

def _engagement(post: dict) -> float:
    comments = int(post.get("댓글수", 0) or 0)
    likes    = int(post.get("추천수", 0) or 0)
    views    = float(post.get("조회수", 0) or 0)
    return comments * 3 + likes * 2 + views * 0.05


def _top_posts(posts: list[dict], n: int = 5) -> list[dict]:
    scored = sorted(posts, key=_engagement, reverse=True)
    result = []
    for p in scored[:n]:
        result.append({
            "제목":   str(p.get("제목", "")),
            "링크":   str(p.get("링크", "")),
            "날짜":   str(p.get("날짜", ""))[:10],
            "댓글수": int(p.get("댓글수", 0) or 0),
            "추천수": int(p.get("추천수", 0) or 0),
            "조회수": int(p.get("조회수", 0) or 0),
            "score":  round(_engagement(p), 1),
        })
    return result


def _calc_issue_score(
    posts_today: list[dict],
    count_today: int,
    avg_7d: float,
) -> int:
    score = 0

    # 1. 게시량 급증
    if avg_7d > 0:
        ratio = count_today / avg_7d
        if ratio >= 2.0:
            score += 3
        elif ratio >= 1.5:
            score += 2
        elif ratio >= 1.2:
            score += 1

    # 2. TOP 게시글 참여도
    if posts_today:
        top = sorted(posts_today, key=_engagement, reverse=True)
        t1_comments = int(top[0].get("댓글수", 0) or 0)
        t1_likes    = int(top[0].get("추천수", 0) or 0)
        if t1_comments >= 30:
            score += 2
        elif t1_comments >= 15:
            score += 1
        if t1_likes >= 15:
            score += 2
        elif t1_likes >= 7:
            score += 1

    return min(score, 10)


# ── 갤러리 단위 분석 ──────────────────────────────────────────────────

def _analyze_gallery(
    gallery: dict,
    target_date: str,
    verbose: bool = False,
) -> dict:
    sheet_url    = gallery["sheet_url"]
    gallery_id   = gallery["gallery_id"]
    gallery_name = gallery["gallery_name"]

    # 오늘 게시글 (전량)
    df_today = reader.get_posts_by_date(sheet_url, target_date)
    posts_today = df_today.to_dict("records") if not df_today.empty else []
    count_today = len(posts_today)

    # 최근 7일 일별 카운트 (오늘 포함)
    daily_counts = reader.get_daily_counts(sheet_url, target_date, lookback_days=7)
    past_counts  = [v for k, v in daily_counts.items() if k != target_date]
    avg_7d       = sum(past_counts) / len(past_counts) if past_counts else 0.0

    issue_score = _calc_issue_score(posts_today, count_today, avg_7d)
    has_issue   = issue_score >= ISSUE_THRESHOLD

    keywords  = kw_mod.extract(posts_today, top_n=10)
    top5      = _top_posts(posts_today, n=5)

    if verbose:
        flag = "🔴 이슈" if has_issue else "✅ 정상"
        print(f"  {gallery_name}: {count_today}건 (평균 {avg_7d:.0f}) → 점수 {issue_score} {flag}")

    return {
        "gallery_id":   gallery_id,
        "gallery_name": gallery_name,
        "posts_total":  count_today,
        "avg_7d":       round(avg_7d, 1),
        "issue_score":  issue_score,
        "has_issue":    has_issue,
        "keywords":     keywords,
        "top_posts":    top5,
        "ai_summary":   "",   # 이슈 판정 후 별도 생성
    }


# ── 메인 진입점 ───────────────────────────────────────────────────────

def run(target_date: str | None = None, verbose: bool = True) -> list[dict]:
    """
    일간 분석 실행.

    Args:
        target_date: 분석 대상 날짜 (YYYY-MM-DD). None이면 어제.
        verbose:     진행 상황 출력 여부.

    Returns:
        갤러리별 분석 결과 리스트.
    """
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if verbose:
        print(f"\n[일간 분석] 대상 날짜: {target_date}")

    galleries = reader.get_gallery_list()
    if not galleries:
        print("  ⚠️  갤러리 목록 없음")
        return []

    results = []
    for g in galleries:
        try:
            result = _analyze_gallery(g, target_date, verbose=verbose)
            results.append(result)
        except Exception as e:
            print(f"  ❌ {g['gallery_name']} 분석 실패: {e}")
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

    # 이슈 갤러리만 AI 요약
    issue_results = [r for r in results if r["has_issue"]]
    if issue_results:
        if verbose:
            print(f"\n[AI 요약] 이슈 갤러리 {len(issue_results)}개 요약 생성 중...")
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
                    print(f"  ✅ {r['gallery_name']} 요약 완료")
            except Exception as e:
                r["ai_summary"] = ""
                print(f"  ❌ {r['gallery_name']} AI 요약 실패: {e}")
    elif verbose:
        print("\n  이슈 갤러리 없음 — AI 요약 생략")

    return results
