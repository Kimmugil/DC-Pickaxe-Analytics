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

    # total_posts: 전체 일 합산
    total_posts = sum(int(r.get("posts_total", 0) or 0) for r in rows)

    # daily_counts: 날짜별 게시글 수
    daily_counts: dict[str, int] = {}
    for r in rows:
        d = str(r.get("date", "")).strip()
        if d:
            daily_counts[d] = int(r.get("posts_total", 0) or 0)

    # top_posts: 이슈 기간 상위 게시글 (댓글+추천 기준 상위 10개, 중복 제목 제거)
    top_posts_all: list[dict] = []
    seen_titles: set[str] = set()
    for r in sorted(issue_rows, key=lambda x: int(x.get("issue_score", 0) or 0), reverse=True):
        tops = _parse_json_field(r.get("top_posts"))
        if not isinstance(tops, list):
            continue
        for p in tops:
            if not isinstance(p, dict):
                continue
            title = str(p.get("제목", "")).strip()
            if title and title not in seen_titles:
                seen_titles.add(title)
                top_posts_all.append(p)
    # 댓글+추천 기준 정렬
    top_posts_all.sort(
        key=lambda p: int(p.get("댓글수", 0) or 0) + int(p.get("추천수", 0) or 0),
        reverse=True,
    )
    top_posts = top_posts_all[:10]

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

    # category_scores 집계 (일간 v2 데이터에서 카테고리별 최고점/발생일수)
    cat_agg: dict[str, dict] = {
        k: {"max_score": 0, "total_score": 0, "issue_days": 0}
        for k in ("balance", "operation", "bug", "payment", "content")
    }
    for r in issue_rows:
        cs = _parse_json_field(r.get("category_scores"))
        if not isinstance(cs, dict) or not cs:
            continue
        for k in cat_agg:
            entry = cs.get(k)
            if isinstance(entry, dict):
                s = int(entry.get("score", 0))
                if s > 0:
                    cat_agg[k]["max_score"]   = max(cat_agg[k]["max_score"], s)
                    cat_agg[k]["total_score"] += s
                    cat_agg[k]["issue_days"]  += 1

    # major_issues 샘플 (일간 major_issues에서 중복 제목 제거 후 상위 5개)
    major_seen: set[str] = set()
    major_issues_sample: list[dict] = []
    for r in sorted(issue_rows, key=lambda x: int(x.get("issue_score", 0) or 0), reverse=True):
        mis = _parse_json_field(r.get("major_issues"))
        if not isinstance(mis, list):
            continue
        for mi in mis:
            if not isinstance(mi, dict):
                continue
            title = str(mi.get("title", "")).strip()
            if title and title not in major_seen:
                major_seen.add(title)
                major_issues_sample.append(mi)
                if len(major_issues_sample) >= 5:
                    break
        if len(major_issues_sample) >= 5:
            break

    return {
        "issue_days":           issue_days,
        "total_issue_score":    total_issue_score,
        "max_issue_score":      max_issue_score,
        "top_cause":            top_cause,
        "total_posts":          total_posts,
        "daily_counts":         daily_counts,
        "top_posts":            top_posts,
        "keywords":             keywords,
        "headlines":            headlines,
        "category_scores_agg":  cat_agg,
        "major_issues_sample":  major_issues_sample,
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
            "gallery_id":           gid,
            "gallery_name":         gallery_names.get(gid, gid),
            "issue_days":           agg["issue_days"],
            "total_issue_score":    agg["total_issue_score"],
            "max_issue_score":      agg["max_issue_score"],
            "top_cause":            agg["top_cause"],
            "total_posts":          agg["total_posts"],
            "daily_counts":         agg["daily_counts"],
            "top_posts":            agg["top_posts"],
            "keywords":             agg["keywords"],
            "headlines":            agg["headlines"],
            "_category_scores_agg": agg["category_scores_agg"],
            "_major_issues_sample": agg["major_issues_sample"],
            "ai_summary":           "",
            # v2 fields (AI 이후 채워짐)
            "headline":        "",
            "category_scores": {},
            "major_issues":    [],
            "sentiment":       {},
        })
        if verbose:
            tag = " (이슈 없음 — AI 제외)" if agg["issue_days"] == 0 else ""
            print(f"  {gallery_names.get(gid, gid)}: 이슈 {agg['issue_days']}일, 최고 {agg['max_issue_score']}점{tag}")

    # AI 요약 v2 (이슈 1일 이상인 갤러리만)
    if verbose:
        print("\n[AI 요약 v2] 갤러리별 월간 요약 생성 중...")
    for i, r in enumerate(results):
        cat_agg  = r.pop("_category_scores_agg", {})
        mis_samp = r.pop("_major_issues_sample", [])

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
            ai = summarize_monthly_gallery(
                gallery_name=r["gallery_name"],
                month=month,
                issue_days=r["issue_days"],
                max_issue_score=r["max_issue_score"],
                top_cause=r["top_cause"],
                keywords=r["keywords"],
                headlines=r["headlines"],
                category_scores_agg=cat_agg,
                major_issues_sample=mis_samp,
            )
            r["ai_summary"]      = ai.get("summary", "")
            r["headline"]        = ai.get("headline", "")
            r["category_scores"] = ai.get("category_scores", {})
            r["major_issues"]    = ai.get("major_issues", [])
            r["sentiment"]       = ai.get("sentiment", {})
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
