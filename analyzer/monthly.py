"""
월간 분석

실행 흐름:
  1. daily_issues Analytics 탭 전체 읽기
  2. 지정 month(YYYY-MM)에 해당하는 행만 필터
  3. 갤러리별 집계: issue_days, total_issue_score, max_issue_score, top_cause, keywords, headlines
  4. Gemini AI 요약 (갤러리별 + 전체 종합)
  5. monthly_issues / monthly_overall 시트에 upsert
"""

from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime, date

from sheets import reader
from analyzer.ai_summary import summarize_monthly_gallery, summarize_monthly_overall


def _parse_json_field(raw) -> list | dict:
    if not raw:
        return []
    if isinstance(raw, (list, dict)):
        return raw
    s = str(raw).strip()
    if not s or s in ("nan", "None", ""):
        return []
    try:
        return json.loads(s)
    except Exception:
        try:
            return json.loads(
                s.replace("'", '"')
                 .replace("True", "true")
                 .replace("False", "false")
                 .replace("None", "null")
            )
        except Exception:
            return []


def get_month_range(month: str | None = None) -> str:
    """month(YYYY-MM)를 반환. None이면 직전 월."""
    if month:
        return month
    today = date.today()
    if today.month == 1:
        return f"{today.year - 1}-12"
    return f"{today.year}-{today.month - 1:02d}"


def _aggregate_gallery(rows: list[dict]) -> dict:
    """특정 갤러리의 일간 이슈 행 목록을 월간 집계로 변환."""
    issue_rows = [r for r in rows if str(r.get("has_issue", "")).strip() == "1"]

    issue_days = len({r["date"] for r in issue_rows if r.get("date")})
    total_issue_score = sum(int(r.get("issue_score", 0) or 0) for r in issue_rows)
    max_issue_score = max((int(r.get("issue_score", 0) or 0) for r in issue_rows), default=0)

    # top_cause: 가장 많이 등장한 issue_cause
    causes = [str(r.get("issue_cause", "")).strip() for r in issue_rows if r.get("issue_cause")]
    top_cause = Counter(causes).most_common(1)[0][0] if causes else ""

    # keywords 합산
    kw_counter: Counter = Counter()
    for r in rows:
        kws = _parse_json_field(r.get("keywords"))
        if isinstance(kws, list):
            for item in kws:
                if isinstance(item, list) and len(item) >= 2:
                    kw_counter[str(item[0])] += int(item[1])
                elif isinstance(item, str):
                    kw_counter[item] += 1
    keywords = kw_counter.most_common(10)

    # headlines: issue 행의 headline 수집
    headlines = []
    seen = set()
    for r in issue_rows:
        h = str(r.get("headline", "")).strip()
        if h and h not in seen:
            seen.add(h)
            headlines.append(h)

    return {
        "issue_days":        issue_days,
        "total_issue_score": total_issue_score,
        "max_issue_score":   max_issue_score,
        "top_cause":         top_cause,
        "keywords":          keywords,
        "headlines":         headlines,
    }


def run(month: str | None = None, verbose: bool = True, dry_run: bool = False) -> dict:
    """
    월간 분석 실행.

    Args:
        month:   분석 대상 월(YYYY-MM). None이면 직전 월.
        verbose: 진행 상황 출력 여부.
        dry_run: True면 시트 쓰기 없이 결과만 반환.

    Returns:
        {
          'month': str,
          'galleries': list[dict],
          'overall_summary': str,
        }
    """
    month = get_month_range(month)

    if verbose:
        print(f"\n[월간 분석] {month}" + (" [DRY-RUN]" if dry_run else ""))

    # daily_issues 전체 로드 후 해당 월 필터
    all_rows = reader.get_all_daily_issues()
    month_rows = [r for r in all_rows if str(r.get("date", "")).startswith(month)]

    if not month_rows:
        print(f"  ⚠️  {month} 데이터 없음")
        return {"month": month, "galleries": [], "overall_summary": ""}

    # 갤러리별 그룹화
    gallery_rows: dict[str, list[dict]] = {}
    gallery_names: dict[str, str] = {}
    for r in month_rows:
        gid = str(r.get("gallery_id", "")).strip()
        if not gid:
            continue
        if gid not in gallery_rows:
            gallery_rows[gid] = []
        gallery_rows[gid].append(r)
        if r.get("gallery_name"):
            gallery_names[gid] = str(r["gallery_name"])

    results = []
    for gid, rows in gallery_rows.items():
        agg = _aggregate_gallery(rows)
        results.append({
            "gallery_id":        gid,
            "gallery_name":      gallery_names.get(gid, gid),
            "issue_days":        agg["issue_days"],
            "total_issue_score": agg["total_issue_score"],
            "max_issue_score":   agg["max_issue_score"],
            "top_cause":         agg["top_cause"],
            "keywords":          agg["keywords"],
            "headlines":         agg["headlines"],
            "ai_summary":        "",
        })
        if verbose:
            tag = " (이슈 없음 — AI 제외)" if agg["issue_days"] == 0 else ""
            print(f"  {gallery_names.get(gid, gid)}: 이슈 {agg['issue_days']}일, 최고 {agg['max_issue_score']}점{tag}")

    # AI 요약 (이슈 1일 이상인 갤러리만)
    if verbose:
        print("\n[AI 요약] 갤러리별 월간 요약 생성 중...")
    for i, r in enumerate(results):
        if r["issue_days"] == 0:
            r["ai_summary"] = "(이슈 없음 — AI 요약 제외)"
            if verbose:
                print(f"  ⏭️  {r['gallery_name']}: 이슈 없음, 요약 제외")
            continue
        if dry_run:
            r["ai_summary"] = "[dry-run]"
            continue
        if i > 0:
            time.sleep(2)
        try:
            r["ai_summary"] = summarize_monthly_gallery(
                gallery_name=r["gallery_name"],
                month=month,
                issue_days=r["issue_days"],
                max_issue_score=r["max_issue_score"],
                top_cause=r["top_cause"],
                keywords=r["keywords"],
                headlines=r["headlines"],
            )
            if verbose:
                print(f"  ✅ {r['gallery_name']}")
        except Exception as e:
            r["ai_summary"] = ""
            print(f"  ❌ {r['gallery_name']} AI 요약 실패: {e}")

    # 전체 종합 AI 요약
    overall_summary = ""
    if not dry_run:
        try:
            if verbose:
                print("\n[AI 요약] 전체 종합 요약 생성 중...")
            overall_summary = summarize_monthly_overall(results, month)
            if verbose:
                print("  ✅ 종합 요약 완료")
        except Exception as e:
            print(f"  ❌ 종합 요약 실패: {e}")
    else:
        overall_summary = "[dry-run]"

    return {
        "month":           month,
        "galleries":       results,
        "overall_summary": overall_summary,
    }
