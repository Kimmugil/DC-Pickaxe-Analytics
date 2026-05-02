"""
일간 이슈 분석

실행 흐름:
  1. 마스터시트에서 갤러리 목록 조회
  2. 갤러리별 target_date 게시글 전량 수집
  3. 요일 보정 기준선 + 모멘텀을 포함한 이슈 점수 계산
  4. 이슈 갤러리 → Gemini AI 요약 생성
  5. 경계(borderline) 갤러리 → 짧은 AI 요약 생성
  6. 전체 결과 반환 (has_issue=0 포함)
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

import pandas as pd

from sheets import reader
from analyzer import keywords as kw_mod
from analyzer.ai_summary import (
    summarize_daily_issue,
    summarize_daily_borderline,
)


ISSUE_THRESHOLD      = 5   # 이슈 판정 최소 점수
BORDERLINE_THRESHOLD = 4   # 경계 판정 최소 점수 (짧은 AI 요약 생성)


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


def _size_thresholds(baseline: float) -> tuple[
    tuple[int, int, int],   # ② 단일 게시글 댓글 기준 (low/mid/high)
    int,                    # ③ 바이럴 판정 댓글 수 기준
    tuple[int, int, int],   # ③ 화제 게시글 수 기준 (low/mid/high)
]:
    """
    갤러리 일평균 게시량(기준선)에 따른 화제성·확산 임계값 반환.
    소규모 갤러리가 절댓값 기준에서 구조적으로 불리한 문제를 보정.

    소규모 (< 30건): 댓글 5/12/25 · 5개↑×1/2/3개
    중규모 (30~100): 댓글 10/20/35 · 8개↑×2/3/4개
    대규모 (100+):   댓글 15/30/50 · 10개↑×2/3/5개 (기존값 유지)
    """
    if baseline < 30:
        return (5, 12, 25), 5, (1, 2, 3)
    elif baseline < 100:
        return (10, 20, 35), 8, (2, 3, 4)
    else:
        return (15, 30, 50), 10, (2, 3, 5)


def _calc_issue_score(
    posts_today: list[dict],
    count_today: int,
    avg_7d: float,
    avg_same_weekday: float = 0.0,
    momentum_avg: float = 0.0,
) -> int:
    """
    이슈 점수 산출 (최대 10점)

    ① 게시량 급증 (0~4점): 기준선 대비 ratio × delta 이중 조건
       - 기준선 = 동요일 4주 평균(우선) 또는 7일 단순 평균
       - min_delta = max(3, baseline × 0.3) 으로 소규모 감도 보정
    ② 단일 게시글 화제성 (0~3점): 최다 댓글 게시글 — 갤러리 규모별 기준
    ③ 바이럴 확산 (0~3점): 화제 게시글 복수 여부 — 갤러리 규모별 기준
    ④ 모멘텀 보너스 (0~1점): 3일 이동평균도 기준선 대비 30% 이상 상승 중
    """
    score = 0

    # 요일 보정 기준선
    baseline = avg_same_weekday if avg_same_weekday > 0 else avg_7d
    # 기준선 없을 때(신규 갤러리)는 오늘 게시량으로 규모 추정
    size_ref = baseline if baseline > 0 else float(count_today)

    # ① 게시량 급증
    if baseline > 0:
        ratio     = count_today / baseline
        delta     = count_today - baseline
        min_delta = max(3.0, baseline * 0.3)
        if ratio >= 3.0 and delta >= min_delta * 2:
            score += 4
        elif ratio >= 2.5 and delta >= min_delta * 1.5:
            score += 3
        elif ratio >= 2.0 and delta >= min_delta:
            score += 2
        elif ratio >= 1.5 and delta >= min_delta * 0.5:
            score += 1

    # 규모별 임계값 결정
    t2, viral_th, t3 = _size_thresholds(size_ref)

    # ② 단일 게시글 화제성
    if posts_today:
        top = sorted(posts_today, key=_engagement, reverse=True)
        t1_comments = int(top[0].get("댓글수", 0) or 0)
        if t1_comments >= t2[2]:
            score += 3
        elif t1_comments >= t2[1]:
            score += 2
        elif t1_comments >= t2[0]:
            score += 1

    # ③ 바이럴 확산
    hot_posts = sum(1 for p in posts_today if int(p.get("댓글수", 0) or 0) >= viral_th)
    if hot_posts >= t3[2]:
        score += 3
    elif hot_posts >= t3[1]:
        score += 2
    elif hot_posts >= t3[0]:
        score += 1

    # ④ 모멘텀 보너스
    if momentum_avg > 0 and baseline > 0 and momentum_avg > baseline * 1.3:
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

    # 7일 단순 평균
    daily_counts = reader.get_daily_counts(sheet_url, target_date, lookback_days=7)
    past_counts  = [v for k, v in daily_counts.items() if k != target_date]
    avg_7d       = sum(past_counts) / len(past_counts) if past_counts else 0.0

    # 동요일 4주 평균 (요일 패턴 보정)
    same_wd          = reader.get_same_weekday_counts(sheet_url, target_date, weeks=4)
    avg_same_weekday = sum(same_wd) / len(same_wd) if same_wd else 0.0

    # 직전 3일 이동평균 (모멘텀)
    recent       = reader.get_recent_daily_counts(sheet_url, target_date, days=3)
    momentum_avg = sum(recent) / len(recent) if recent else 0.0

    issue_score   = _calc_issue_score(posts_today, count_today, avg_7d, avg_same_weekday, momentum_avg)
    has_issue     = issue_score >= ISSUE_THRESHOLD
    is_borderline = (not has_issue) and (issue_score >= BORDERLINE_THRESHOLD)

    keywords = kw_mod.extract(posts_today, top_n=10)
    top5     = _issue_posts(posts_today, n=5)

    if verbose:
        flag = "이슈" if has_issue else ("경계" if is_borderline else "정상")
        baseline_val = avg_same_weekday if avg_same_weekday > 0 else avg_7d
        size_label = "소규모" if baseline_val < 30 else ("중규모" if baseline_val < 100 else "대규모")
        print(
            f"  {gallery_name} [{size_label}]: {count_today}건 "
            f"(7일평균 {avg_7d:.0f} / 동요일평균 {avg_same_weekday:.0f}) "
            f"점수:{issue_score} {flag}",
            flush=True,
        )

    return {
        "gallery_id":       gallery_id,
        "gallery_name":     gallery_name,
        "posts_total":      count_today,
        "avg_7d":           round(avg_7d, 1),
        "avg_same_weekday": round(avg_same_weekday, 1),
        "momentum_avg":     round(momentum_avg, 1),
        "issue_score":      issue_score,
        "has_issue":        has_issue,
        "is_borderline":    is_borderline,
        "keywords":         keywords,
        "top_posts":        top5,
        "ai_summary":       "",
        "temperature_tag":  "",
        "issue_cause":      "",
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
            time.sleep(2)
        try:
            result = _analyze_gallery(g, target_date, verbose=verbose)
            results.append(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  실패: {g['gallery_name']} - {e}", flush=True)
            results.append({
                "gallery_id":       g["gallery_id"],
                "gallery_name":     g["gallery_name"],
                "posts_total":      0,
                "avg_7d":           0.0,
                "avg_same_weekday": 0.0,
                "momentum_avg":     0.0,
                "issue_score":      0,
                "has_issue":        False,
                "is_borderline":    False,
                "keywords":         [],
                "top_posts":        [],
                "ai_summary":       "",
                "temperature_tag":  "",
                "issue_cause":      "",
            })

    # 이슈 갤러리 AI 요약
    issue_results = [r for r in results if r["has_issue"]]
    if issue_results:
        print(f"\n[AI 요약] 이슈 갤러리 {len(issue_results)}개...", flush=True)
        for r in issue_results:
            try:
                ai = summarize_daily_issue(
                    gallery_name=r["gallery_name"],
                    top_posts=r["top_posts"],
                    keywords=r["keywords"],
                    issue_score=r["issue_score"],
                    count_today=r["posts_total"],
                    avg_7d=r["avg_7d"],
                )
                r["ai_summary"]      = ai.get("summary", "")
                r["temperature_tag"] = ai.get("temperature_tag", "")
                r["issue_cause"]     = ai.get("issue_cause", "기타")
                if verbose:
                    print(f"  완료: {r['gallery_name']} [{r['temperature_tag']}]", flush=True)
            except Exception as e:
                r["ai_summary"] = ""
                print(f"  AI 요약 실패: {r['gallery_name']} - {e}", flush=True)
    elif verbose:
        print("  이슈 갤러리 없음 - AI 요약 생략", flush=True)

    # 경계 갤러리 짧은 AI 요약
    borderline_results = [r for r in results if r.get("is_borderline")]
    if borderline_results:
        print(f"\n[AI 요약] 경계 갤러리 {len(borderline_results)}개 (짧은 요약)...", flush=True)
        for r in borderline_results:
            try:
                avg_baseline = max(r["avg_7d"], r.get("avg_same_weekday", 0.0))
                ai = summarize_daily_borderline(
                    gallery_name=r["gallery_name"],
                    top_posts=r["top_posts"],
                    keywords=r["keywords"],
                    issue_score=r["issue_score"],
                    count_today=r["posts_total"],
                    avg_baseline=avg_baseline,
                )
                r["ai_summary"]      = ai.get("summary", "")
                r["temperature_tag"] = ai.get("temperature_tag", "")
                if verbose:
                    print(f"  완료(경계): {r['gallery_name']} [{r['temperature_tag']}]", flush=True)
            except Exception as e:
                r["ai_summary"] = ""
                print(f"  AI 요약 실패(경계): {r['gallery_name']} - {e}", flush=True)

    return results
