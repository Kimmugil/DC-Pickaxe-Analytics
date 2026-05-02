"""
온도감 태그(temperature_tag) + 이슈 원인(issue_cause) 백필 스크립트

daily_issues 시트에서 has_issue/is_borderline=1이지만
temperature_tag가 비어있는 행을 찾아 AI 태그를 재생성합니다.

사용법:
  python backfill_tags.py                  # 전체 백필
  python backfill_tags.py --limit 20       # 최대 20행만 처리
  python backfill_tags.py --dry-run        # 대상 목록만 확인 (실제 쓰기 안 함)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

import gspread
from google.oauth2.service_account import Credentials

from analyzer.ai_summary import summarize_daily_issue, summarize_daily_borderline

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ISSUE_THRESHOLD      = 5
BORDERLINE_THRESHOLD = 4


def _client() -> gspread.Client:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        creds = Credentials.from_service_account_info(json.loads(raw), scopes=_SCOPES)
    else:
        path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
        creds = Credentials.from_service_account_file(path, scopes=_SCOPES)
    return gspread.authorize(creds)


def _parse_field(v: str) -> list:
    if not v or v in ("nan", "None", "[]"):
        return []
    try:
        return json.loads(v)
    except Exception:
        try:
            return json.loads(
                v.replace("'", '"')
                 .replace("True", "true")
                 .replace("False", "false")
                 .replace("None", "null")
            )
        except Exception:
            return []


def _parse_bool(v: str) -> bool:
    return v.strip().lower() in ("1", "true")


def main() -> None:
    parser = argparse.ArgumentParser(description="temperature_tag/issue_cause 백필")
    parser.add_argument("--limit",   type=int, default=0,    help="처리할 최대 행 수 (0=전체)")
    parser.add_argument("--dry-run", action="store_true",    help="대상 목록만 출력, 실제 쓰기 안 함")
    args = parser.parse_args()

    sh = _client().open_by_key(os.environ["ANALYTICS_SPREADSHEET_ID"])
    ws = sh.worksheet("daily_issues")

    all_values = ws.get_all_values()
    if not all_values:
        print("시트가 비어 있습니다.")
        sys.exit(0)

    headers = all_values[0]
    print(f"헤더: {headers}")

    # temperature_tag / issue_cause 컬럼 위치 확인 (없으면 추가)
    if "temperature_tag" not in headers:
        headers.append("temperature_tag")
        ws.update("A1", [headers])
        print("  ▶ temperature_tag 헤더 추가")
    if "issue_cause" not in headers:
        headers.append("issue_cause")
        ws.update("A1", [headers])
        print("  ▶ issue_cause 헤더 추가")

    col = {h: i for i, h in enumerate(headers)}

    def get(row: list, key: str) -> str:
        i = col.get(key)
        return row[i] if i is not None and i < len(row) else ""

    # 백필 대상 수집
    targets = []
    for row_idx, row in enumerate(all_values[1:], start=2):  # 1-indexed, row 1 = header
        has_issue    = _parse_bool(get(row, "has_issue"))
        is_borderline = _parse_bool(get(row, "is_borderline"))
        if not (has_issue or is_borderline):
            continue
        if get(row, "temperature_tag"):  # 이미 있으면 건너뜀
            continue
        targets.append((row_idx, row))

    print(f"\n백필 대상: {len(targets)}행")
    if args.limit and len(targets) > args.limit:
        targets = targets[:args.limit]
        print(f"  → --limit {args.limit}으로 제한")

    if args.dry_run:
        for row_idx, row in targets:
            print(f"  행{row_idx:4d}  {get(row, 'date')}  {get(row, 'gallery_name')}")
        return

    tag_col_letter = _col_letter(col["temperature_tag"] + 1)
    cause_col_letter = _col_letter(col["issue_cause"] + 1)

    processed = 0
    for i, (row_idx, row) in enumerate(targets):
        if i > 0:
            time.sleep(3)

        has_issue     = _parse_bool(get(row, "has_issue"))
        is_borderline = _parse_bool(get(row, "is_borderline"))
        gallery_name  = get(row, "gallery_name")
        date          = get(row, "date")
        issue_score   = int(get(row, "issue_score") or "0")
        posts_total   = int(get(row, "posts_total") or "0")
        avg_7d        = float(get(row, "avg_7d") or "0")
        keywords      = _parse_field(get(row, "keywords"))
        top_posts     = _parse_field(get(row, "top_posts"))

        print(f"  [{i+1}/{len(targets)}] {date} {gallery_name} (행{row_idx})", end=" ... ", flush=True)

        try:
            if has_issue:
                ai = summarize_daily_issue(
                    gallery_name=gallery_name,
                    top_posts=top_posts,
                    keywords=keywords,
                    issue_score=issue_score,
                    count_today=posts_total,
                    avg_7d=avg_7d,
                )
            else:
                avg_baseline = max(avg_7d, float(get(row, "avg_same_weekday") or "0"))
                ai = summarize_daily_borderline(
                    gallery_name=gallery_name,
                    top_posts=top_posts,
                    keywords=keywords,
                    issue_score=issue_score,
                    count_today=posts_total,
                    avg_baseline=avg_baseline,
                )

            temperature_tag = ai.get("temperature_tag", "")
            issue_cause     = ai.get("issue_cause", "") if has_issue else ""

            # 시트 업데이트 (temperature_tag, issue_cause 두 셀)
            ws.update(f"{tag_col_letter}{row_idx}", [[temperature_tag]])
            if has_issue and issue_cause:
                ws.update(f"{cause_col_letter}{row_idx}", [[issue_cause]])

            print(f"완료 [{temperature_tag}] {issue_cause}")
            processed += 1

        except Exception as e:
            print(f"실패: {e}")

    print(f"\n✅ 백필 완료: {processed}/{len(targets)}행")


def _col_letter(n: int) -> str:
    """1-indexed 컬럼 번호 → 엑셀 컬럼 문자 (A, B, ..., Z, AA, ...)"""
    result = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        result = chr(65 + r) + result
    return result


if __name__ == "__main__":
    main()
