"""
Google Sheets 쓰기 모듈 — Analytics 전용

대상 시트 (DC-Pickaxe Analytics 스프레드시트):
  - daily_issues      : 일간 이슈 분석 결과
  - weekly_galleries  : 주간 갤러리별 분석 결과
  - weekly_overall    : 주간 전체 종합 요약
"""

import os
import json

import gspread
from google.oauth2.service_account import Credentials

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

_HEADERS = {
    "daily_issues": [
        "date", "run_id", "gallery_id", "gallery_name",
        "posts_total", "avg_7d", "issue_score", "has_issue",
        "keywords", "top_posts", "ai_summary",
    ],
    "weekly_galleries": [
        "week_start", "week_end", "run_id", "gallery_id", "gallery_name",
        "total_posts", "daily_counts", "keywords", "top_posts", "ai_summary",
    ],
    "weekly_overall": [
        "week_start", "week_end", "run_id", "ai_summary",
    ],
}


_gc: gspread.Client | None = None


def _client() -> gspread.Client:
    """모듈 레벨 싱글턴 gspread 클라이언트."""
    global _gc
    if _gc is None:
        raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
        if raw:
            info = json.loads(raw)
            creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
        else:
            path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
            creds = Credentials.from_service_account_file(path, scopes=_SCOPES)
        _gc = gspread.authorize(creds)
    return _gc


def _spreadsheet() -> gspread.Spreadsheet:
    return _client().open_by_key(os.environ["ANALYTICS_SPREADSHEET_ID"])


# ── 시트 초기화 ───────────────────────────────────────────────────────

def setup_sheets() -> None:
    """
    Analytics 스프레드시트 초기화.
    신규 시트 먼저 생성 → 구 시트 삭제 (1개 남은 시트 삭제 불가 문제 방지).
    """
    sh = _spreadsheet()
    existing = {ws.title for ws in sh.worksheets()}

    # 1단계: 신규 시트 먼저 생성
    for name, headers in _HEADERS.items():
        if name in existing:
            ws = sh.worksheet(name)
            if ws.row_values(1) != headers:
                ws.clear()
                ws.append_row(headers, value_input_option="RAW")
                print(f"  [헤더 재설정] {name}")
            else:
                print(f"  [유지] {name}")
        else:
            ws = sh.add_worksheet(title=name, rows=5000, cols=len(headers))
            ws.append_row(headers, value_input_option="RAW")
            print(f"  [생성] {name}")

    # 2단계: 구 시트 삭제 (이제 새 시트가 있으므로 안전하게 삭제 가능)
    existing = {ws.title for ws in sh.worksheets()}  # 갱신
    old = {"분석결과", "분석결果", "분석결과", "분석결과",
           "분석대상게시글", "분석대상게시글",
           "종합요약", "주간분석", "주간분석", "주간종합", "시트1"}
    for title in old & existing:
        sh.del_worksheet(sh.worksheet(title))
        print(f"  [삭제] {title}")


# ── 일간 이슈 적재 ────────────────────────────────────────────────────

def append_daily_issues(results: list[dict], date: str, run_id: str) -> None:
    """
    daily_issues 시트에 일간 분석 결과를 추가합니다.
    has_issue=0 인 갤러리도 포함 (전체 기록 유지).
    """
    ws = _spreadsheet().worksheet("daily_issues")
    rows = [
        [
            date, run_id,
            r.get("gallery_id", ""), r.get("gallery_name", ""),
            r.get("posts_total", 0), round(float(r.get("avg_7d", 0)), 1),
            r.get("issue_score", 0), 1 if r.get("has_issue") else 0,
            json.dumps(r.get("keywords", []), ensure_ascii=False),
            json.dumps(r.get("top_posts", []), ensure_ascii=False),
            r.get("ai_summary", ""),
        ]
        for r in results
    ]
    if rows:
        ws.append_rows(rows, value_input_option="RAW")


# ── 주간 갤러리별 적재 ────────────────────────────────────────────────

def append_weekly_galleries(
    results: list[dict], week_start: str, week_end: str, run_id: str
) -> None:
    """weekly_galleries 시트에 주간 갤러리별 분석 결과를 추가합니다."""
    ws = _spreadsheet().worksheet("weekly_galleries")
    rows = [
        [
            week_start, week_end, run_id,
            r.get("gallery_id", ""), r.get("gallery_name", ""),
            r.get("total_posts", 0),
            json.dumps(r.get("daily_counts", {}), ensure_ascii=False),
            json.dumps(r.get("keywords", []), ensure_ascii=False),
            json.dumps(r.get("top_posts", []), ensure_ascii=False),
            r.get("ai_summary", ""),
        ]
        for r in results
    ]
    if rows:
        ws.append_rows(rows, value_input_option="RAW")


# ── 주간 종합 요약 적재 ───────────────────────────────────────────────

def append_weekly_overall(
    ai_summary: str, week_start: str, week_end: str, run_id: str
) -> None:
    """weekly_overall 시트에 주간 종합 요약을 추가합니다."""
    _spreadsheet().worksheet("weekly_overall").append_row(
        [week_start, week_end, run_id, ai_summary],
        value_input_option="RAW",
    )
