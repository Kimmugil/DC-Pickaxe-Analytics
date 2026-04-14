"""
주간 분석

실행 흐름:
  1. 마스터시트에서 갤러리 목록 조회
  2. 갤러리별 week_start~week_end 게시글 전량 수집
  3. 게시량 집계 / 일별 추이 / 키워드 / TOP 5 게시글
  4. Gemini AI 요약 (갤러리별 + 전체 종합)
  5. 전체 결과 반환
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta

import pandas as pd

from sheets import reader
from analyzer import keywords as kw_mod
from analyzer.ai_summary import summarize_weekly_gallery, summarize_weekly_overall


def _engagement(post: dict) -> float:
    return (int(post.get("댓글수", 0) or 0) * 3
            + int(post.get("추천수", 0) or 0) * 2
            + float(post.get("조회수", 0) or 0) * 0.05)


def _top_posts(posts: list[dict], n: int = 5) -> list[dict]:
    scored = sorted(posts, key=_engagement, reverse=True)
    return [
        {
            "제목":   str(p.get("제목", "")),
            "링크":   str(p.get("링크", "")),
            "날짜":   str(p.get("날짜", ""))[:10],
            "댓글수": int(p.get("댓글수", 0) or 0),
            "추천수": int(p.get("추천수", 0) or 0),
            "조회수": int(p.get("조회수", 0) or 0),
            "score":  round(_engagement(p), 1),
        }
        for p in scored[:n]
    ]


def _analyze_gallery(
    gallery: dict,
    week_start: str,
    week_end: str,
    verbose: bool = False,
) -> dict:
    df = reader.get_posts_date_range(gallery["sheet_url"], week_start, week_end)
    posts = df.to_dict("records") if not df.empty else []
    total = len(posts)

    # 일별 게시글 수 — 주간 전 날짜(7일) 0으로 초기화 후 실제값 덮어쓰기
    # (게시글 없는 날도 막대 차트에 0으로 표시되도록)
    from datetime import date as _date
    _ws = datetime.strptime(week_start, "%Y-%m-%d").date()
    _we = datetime.strptime(week_end,   "%Y-%m-%d").date()
    daily_counts: dict[str, int] = {}
    _cur = _ws
    while _cur <= _we:
        daily_counts[str(_cur)] = 0
        _cur += timedelta(days=1)
    if not df.empty and "날짜" in df.columns:
        for _d, _c in df.groupby(df["날짜"].dt.date).size().items():
            if str(_d) in daily_counts:
                daily_counts[str(_d)] = int(_c)

    keywords = kw_mod.extract(posts, top_n=10)
    top5     = _top_posts(posts, n=5)

    if verbose:
        tag = " (저활동 — AI 요약 제외)" if total < 10 else ""
        print(f"  {gallery['gallery_name']}: {total}건{tag}")

    return {
        "gallery_id":   gallery["gallery_id"],
        "gallery_name": gallery["gallery_name"],
        "total_posts":  total,
        "daily_counts": daily_counts,
        "keywords":     keywords,
        "top_posts":    top5,
        "ai_summary":   "",
    }


# ── 주 범위 헬퍼 ──────────────────────────────────────────────────────

def get_week_range(week_start: str | None = None) -> tuple[str, str]:
    """
    week_start(월요일)을 받아 (week_start, week_end) 반환.
    None이면 지난 주 월~일.
    """
    if week_start:
        s = datetime.strptime(week_start, "%Y-%m-%d")
    else:
        today = datetime.now()
        s = today - timedelta(days=today.weekday() + 7)  # 지난 주 월요일
    e = s + timedelta(days=6)
    return s.strftime("%Y-%m-%d"), e.strftime("%Y-%m-%d")


# ── 메인 진입점 ───────────────────────────────────────────────────────

def run(week_start: str | None = None, verbose: bool = True) -> dict:
    """
    주간 분석 실행.

    Args:
        week_start: 분석 주 시작일(월요일, YYYY-MM-DD). None이면 지난 주.
        verbose:    진행 상황 출력 여부.

    Returns:
        {
          'week_start': str,
          'week_end':   str,
          'galleries':  list[dict],   # 갤러리별 결과
          'overall_summary': str,     # 전체 AI 종합 요약
        }
    """
    week_start, week_end = get_week_range(week_start)

    if verbose:
        print(f"\n[주간 분석] {week_start} ~ {week_end}")

    galleries = reader.get_gallery_list()
    if not galleries:
        print("  ⚠️  갤러리 목록 없음")
        return {"week_start": week_start, "week_end": week_end,
                "galleries": [], "overall_summary": ""}

    results = []
    for i, g in enumerate(galleries):
        if i > 0:
            time.sleep(2)  # 갤러리 간 2초 딜레이 (429 방지)
        try:
            r = _analyze_gallery(g, week_start, week_end, verbose=verbose)
            results.append(r)
        except Exception as e:
            print(f"  ❌ {g['gallery_name']} 분석 실패: {e}")
            results.append({
                "gallery_id":   g["gallery_id"],
                "gallery_name": g["gallery_name"],
                "total_posts":  0,
                "daily_counts": {},
                "keywords":     [],
                "top_posts":    [],
                "ai_summary":   "",
            })

    # 갤러리별 AI 요약 (10건 미만은 제외)
    if verbose:
        print("\n[AI 요약] 갤러리별 주간 요약 생성 중...")
    for r in results:
        if r["total_posts"] < 10:
            r["ai_summary"] = "(주간 게시글 10건 미만 — AI 요약 제외)"
            if verbose:
                print(f"  ⏭️  {r['gallery_name']}: 10건 미만, 요약 제외")
            continue
        try:
            r["ai_summary"] = summarize_weekly_gallery(
                gallery_name=r["gallery_name"],
                total_posts=r["total_posts"],
                top_posts=r["top_posts"],
                keywords=r["keywords"],
                week_start=week_start,
                week_end=week_end,
            )
            if verbose:
                print(f"  ✅ {r['gallery_name']}")
        except Exception as e:
            r["ai_summary"] = ""
            print(f"  ❌ {r['gallery_name']} AI 요약 실패: {e}")

    # 전체 종합 AI 요약
    overall_summary = ""
    try:
        if verbose:
            print("\n[AI 요약] 전체 종합 요약 생성 중...")
        overall_summary = summarize_weekly_overall(results, week_start, week_end)
        if verbose:
            print("  ✅ 종합 요약 완료")
    except Exception as e:
        print(f"  ❌ 종합 요약 실패: {e}")

    return {
        "week_start":      week_start,
        "week_end":        week_end,
        "galleries":       results,
        "overall_summary": overall_summary,
    }
