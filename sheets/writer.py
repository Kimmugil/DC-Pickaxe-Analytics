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
        "temperature_tag", "issue_cause",
        # v2: 구조화 분석 필드
        "headline", "category_scores", "major_issues",
        "sentiment_positive", "sentiment_negative",
        # v2.1: 추가 지표 (기존 시트에 컬럼이 없으면 _ensure_headers가 끝에 추가)
        "avg_same_weekday", "momentum_avg", "is_borderline",
    ],
    "weekly_galleries": [
        "week_start", "week_end", "run_id", "gallery_id", "gallery_name",
        "total_posts", "daily_counts", "keywords", "top_posts", "ai_summary",
        # v2: 구조화 분석 필드
        "headline", "category_scores", "major_issues",
        "sentiment_positive", "sentiment_negative", "temperature_tag",
    ],
    "weekly_overall": [
        "week_start", "week_end", "run_id", "ai_summary",
    ],
    "monthly_issues": [
        "month", "run_id", "gallery_id", "gallery_name",
        "issue_days", "total_issue_score", "max_issue_score",
        "top_cause", "total_posts", "daily_counts", "top_posts",
        "keywords", "headlines", "ai_summary",
        # v2: 구조화 분석 필드
        "headline", "category_scores", "major_issues",
        "sentiment_positive", "sentiment_negative",
    ],
    "monthly_overall": [
        "month", "run_id", "ai_summary",
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


# ── 헤더 마이그레이션 ─────────────────────────────────────────────────

def _ensure_headers(ws: "gspread.Worksheet", expected: list[str]) -> None:
    """기존 시트를 지우지 않고 누락된 컬럼만 헤더 행에 추가한다."""
    current = ws.row_values(1)
    missing = [h for h in expected if h not in current]
    if missing:
        new_headers = current + missing
        ws.update("A1", [new_headers])


# ── 일간 이슈 적재 ────────────────────────────────────────────────────

def append_daily_issues(results: list[dict], date: str, run_id: str) -> None:
    """
    daily_issues 시트에 일간 분석 결과를 추가합니다.
    has_issue=0 인 갤러리도 포함 (전체 기록 유지).
    """
    ws = _spreadsheet().worksheet("daily_issues")
    _ensure_headers(ws, _HEADERS["daily_issues"])
    headers = ws.row_values(1)
    rows = [_build_daily_row(r, date, run_id, headers) for r in results]
    if rows:
        ws.append_rows(rows, value_input_option="RAW")


# ── 일간 이슈 재분석 upsert ───────────────────────────────────────────

def upsert_daily_issues(results: list[dict], date: str, run_id: str) -> None:
    """
    daily_issues 시트에 재분석 결과를 upsert합니다.
    (date, gallery_id) 기준으로 기존 행이 있으면 덮어쓰고, 없으면 추가합니다.
    백필 재분석 전용.
    """
    ws = _spreadsheet().worksheet("daily_issues")
    _ensure_headers(ws, _HEADERS["daily_issues"])

    all_values = ws.get_all_values()
    headers = all_values[0] if all_values else []
    col = {h: i for i, h in enumerate(headers)}

    # (date, gallery_id) → 1-indexed 행 번호 맵핑
    row_map: dict[tuple[str, str], int] = {}
    for row_idx, row in enumerate(all_values[1:], start=2):
        d   = row[col["date"]]      if "date"       in col and col["date"]       < len(row) else ""
        gid = row[col["gallery_id"]] if "gallery_id" in col and col["gallery_id"] < len(row) else ""
        if d and gid:
            row_map[(d, gid)] = row_idx

    new_rows: list[dict] = []
    update_batch: list[tuple[int, list]] = []

    for r in results:
        row_data = _build_daily_row(r, date, run_id, headers)
        key = (date, r.get("gallery_id", ""))
        if key in row_map:
            update_batch.append((row_map[key], row_data))
        else:
            new_rows.append(r)

    # 기존 행 업데이트 (행 단위 batch)
    for row_idx, row_data in update_batch:
        ws.update(f"A{row_idx}", [row_data])

    # 신규 행 append
    if new_rows:
        append_rows = [_build_daily_row(r, date, run_id, headers) for r in new_rows]
        ws.append_rows(append_rows, value_input_option="RAW")

    print(f"  upsert: {len(update_batch)}행 업데이트 / {len(new_rows)}행 신규 추가", flush=True)


def _build_daily_row(r: dict, date: str, run_id: str, headers: list[str]) -> list:
    """
    daily_issues 헤더 목록에 맞는 행 데이터를 컬럼명 기반으로 반환합니다.
    컬럼 순서가 달라도 올바른 열에 데이터가 기록됩니다.
    """
    sentiment = r.get("sentiment", {})
    data_map: dict[str, object] = {
        "date":               date,
        "run_id":             run_id,
        "gallery_id":         r.get("gallery_id", ""),
        "gallery_name":       r.get("gallery_name", ""),
        "posts_total":        r.get("posts_total", 0),
        "avg_7d":             round(float(r.get("avg_7d", 0)), 1),
        "avg_same_weekday":   round(float(r.get("avg_same_weekday", 0)), 1),
        "momentum_avg":       round(float(r.get("momentum_avg", 0)), 1),
        "issue_score":        r.get("issue_score", 0),
        "has_issue":          1 if r.get("has_issue") else 0,
        "is_borderline":      1 if r.get("is_borderline") else 0,
        "keywords":           json.dumps(r.get("keywords", []), ensure_ascii=False),
        "top_posts":          json.dumps(r.get("top_posts", []), ensure_ascii=False),
        "ai_summary":         r.get("ai_summary", ""),
        "temperature_tag":    r.get("temperature_tag", ""),
        "issue_cause":        r.get("issue_cause", ""),
        "headline":           r.get("headline", ""),
        "category_scores":    json.dumps(r.get("category_scores", {}), ensure_ascii=False),
        "major_issues":       json.dumps(r.get("major_issues", []), ensure_ascii=False),
        "sentiment_positive": sentiment.get("positive", "") if isinstance(sentiment, dict) else "",
        "sentiment_negative": sentiment.get("negative", "") if isinstance(sentiment, dict) else "",
    }
    return [data_map.get(h, "") for h in headers]


# ── 주간 갤러리별 적재 ────────────────────────────────────────────────

def _build_weekly_row(r: dict, week_start: str, week_end: str, run_id: str, total_cols: int) -> list:
    """weekly_galleries 헤더 순서에 맞는 행 데이터를 반환합니다."""
    base = [
        week_start, week_end, run_id,
        r.get("gallery_id", ""), r.get("gallery_name", ""),
        r.get("total_posts", 0),
        json.dumps(r.get("daily_counts", {}), ensure_ascii=False),
        json.dumps(r.get("keywords", []), ensure_ascii=False),
        json.dumps(r.get("top_posts", []), ensure_ascii=False),
        r.get("ai_summary", ""),
        # v2
        r.get("headline", ""),
        json.dumps(r.get("category_scores", {}), ensure_ascii=False),
        json.dumps(r.get("major_issues", []), ensure_ascii=False),
        r.get("sentiment", {}).get("positive", "") if isinstance(r.get("sentiment"), dict) else "",
        r.get("sentiment", {}).get("negative", "") if isinstance(r.get("sentiment"), dict) else "",
        r.get("temperature_tag", ""),
    ]
    while len(base) < total_cols:
        base.append("")
    return base


def append_weekly_galleries(
    results: list[dict], week_start: str, week_end: str, run_id: str
) -> None:
    """weekly_galleries 시트에 주간 갤러리별 분석 결과를 추가합니다."""
    ws = _spreadsheet().worksheet("weekly_galleries")
    _ensure_headers(ws, _HEADERS["weekly_galleries"])
    headers = ws.row_values(1)
    rows = [_build_weekly_row(r, week_start, week_end, run_id, len(headers)) for r in results]
    if rows:
        ws.append_rows(rows, value_input_option="RAW")


def upsert_weekly_galleries(
    results: list[dict], week_start: str, week_end: str, run_id: str
) -> None:
    """
    weekly_galleries 시트에 주간 갤러리별 분석 결과를 upsert합니다.
    (week_start, gallery_id) 기준으로 기존 행이 있으면 덮어쓰고, 없으면 추가합니다.
    백필 재분석 전용.
    """
    ws = _spreadsheet().worksheet("weekly_galleries")
    _ensure_headers(ws, _HEADERS["weekly_galleries"])

    all_values = ws.get_all_values()
    headers = all_values[0] if all_values else []
    col = {h: i for i, h in enumerate(headers)}

    row_map: dict[tuple[str, str], int] = {}
    for row_idx, row in enumerate(all_values[1:], start=2):
        ws_val = row[col["week_start"]] if "week_start" in col and col["week_start"] < len(row) else ""
        gid    = row[col["gallery_id"]] if "gallery_id" in col and col["gallery_id"] < len(row) else ""
        if ws_val and gid:
            row_map[(ws_val, gid)] = row_idx

    new_rows: list[list] = []
    update_batch: list[tuple[int, list]] = []

    for r in results:
        row_data = _build_weekly_row(r, week_start, week_end, run_id, len(headers))
        key = (week_start, r.get("gallery_id", ""))
        if key in row_map:
            update_batch.append((row_map[key], row_data))
        else:
            new_rows.append(row_data)

    for row_idx, row_data in update_batch:
        ws.update(f"A{row_idx}", [row_data])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")

    print(f"  [weekly_galleries] upsert: {len(update_batch)}행 업데이트 / {len(new_rows)}행 신규 추가", flush=True)


# ── 주간 종합 요약 적재 ───────────────────────────────────────────────

def append_weekly_overall(
    ai_summary: str, week_start: str, week_end: str, run_id: str
) -> None:
    """weekly_overall 시트에 주간 종합 요약을 추가합니다."""
    _spreadsheet().worksheet("weekly_overall").append_row(
        [week_start, week_end, run_id, ai_summary],
        value_input_option="RAW",
    )


# ── 월간 시트 초기화 ──────────────────────────────────────────────────

def _get_or_create_worksheet(sh: gspread.Spreadsheet, name: str, headers: list[str]) -> "gspread.Worksheet":
    """시트가 없으면 생성하고, 있으면 헤더만 확인."""
    existing = {ws.title for ws in sh.worksheets()}
    if name not in existing:
        ws = sh.add_worksheet(title=name, rows=2000, cols=len(headers))
        ws.append_row(headers, value_input_option="RAW")
        print(f"  [생성] {name}")
    else:
        ws = sh.worksheet(name)
        _ensure_headers(ws, headers)
    return ws


def setup_monthly_sheets() -> None:
    """monthly_issues / monthly_overall 시트를 생성/초기화합니다."""
    sh = _spreadsheet()
    for name in ("monthly_issues", "monthly_overall"):
        _get_or_create_worksheet(sh, name, _HEADERS[name])
        print(f"  [완료] {name}")


# ── 월간 갤러리별 upsert ──────────────────────────────────────────────

def upsert_monthly_issues(results: list[dict], month: str, run_id: str) -> None:
    """
    monthly_issues 시트에 월간 갤러리별 분석 결과를 upsert합니다.
    (month, gallery_id) 기준.
    """
    sh = _spreadsheet()
    ws = _get_or_create_worksheet(sh, "monthly_issues", _HEADERS["monthly_issues"])

    all_values = ws.get_all_values()
    headers = all_values[0] if all_values else []
    col = {h: i for i, h in enumerate(headers)}

    row_map: dict[tuple[str, str], int] = {}
    for row_idx, row in enumerate(all_values[1:], start=2):
        m   = row[col["month"]]      if "month"       in col and col["month"]       < len(row) else ""
        gid = row[col["gallery_id"]] if "gallery_id"  in col and col["gallery_id"]  < len(row) else ""
        if m and gid:
            row_map[(m, gid)] = row_idx

    new_rows: list[list] = []
    update_batch: list[tuple[int, list]] = []

    for r in results:
        # 헤더 목록을 전달해 컬럼명 기반으로 데이터 위치 결정 (컬럼 순서 불일치 방지)
        row_data = _build_monthly_row(r, month, run_id, headers)
        key = (month, r.get("gallery_id", ""))
        if key in row_map:
            update_batch.append((row_map[key], row_data))
        else:
            new_rows.append(row_data)

    for row_idx, row_data in update_batch:
        ws.update(f"A{row_idx}", [row_data])

    if new_rows:
        ws.append_rows(new_rows, value_input_option="RAW")

    print(f"  [monthly_issues] upsert: {len(update_batch)}행 업데이트 / {len(new_rows)}행 신규 추가", flush=True)


def _build_monthly_row(r: dict, month: str, run_id: str, headers: list[str]) -> list:
    """
    monthly_issues 헤더 목록에 맞는 행 데이터를 컬럼명 기반으로 반환합니다.
    컬럼 순서가 달라도 올바른 열에 데이터가 기록됩니다.
    """
    sentiment = r.get("sentiment", {})
    data_map: dict[str, object] = {
        "month":              month,
        "run_id":             run_id,
        "gallery_id":         r.get("gallery_id", ""),
        "gallery_name":       r.get("gallery_name", ""),
        "issue_days":         r.get("issue_days", 0),
        "total_issue_score":  r.get("total_issue_score", 0),
        "max_issue_score":    r.get("max_issue_score", 0),
        "top_cause":          r.get("top_cause", ""),
        "total_posts":        r.get("total_posts", 0),
        "daily_counts":       json.dumps(r.get("daily_counts", {}), ensure_ascii=False),
        "top_posts":          json.dumps(r.get("top_posts", []),    ensure_ascii=False),
        "keywords":           json.dumps(r.get("keywords", []),     ensure_ascii=False),
        "headlines":          json.dumps(r.get("headlines", []),    ensure_ascii=False),
        "ai_summary":         r.get("ai_summary", ""),
        "headline":           r.get("headline", ""),
        "category_scores":    json.dumps(r.get("category_scores", {}), ensure_ascii=False),
        "major_issues":       json.dumps(r.get("major_issues", []),    ensure_ascii=False),
        "sentiment_positive": sentiment.get("positive", "") if isinstance(sentiment, dict) else "",
        "sentiment_negative": sentiment.get("negative", "") if isinstance(sentiment, dict) else "",
    }
    return [data_map.get(h, "") for h in headers]


# ── 월간 종합 요약 upsert ─────────────────────────────────────────────

def upsert_monthly_overall(ai_summary: str, month: str, run_id: str) -> None:
    """monthly_overall 시트에 월간 종합 요약을 upsert합니다."""
    sh = _spreadsheet()
    ws = _get_or_create_worksheet(sh, "monthly_overall", _HEADERS["monthly_overall"])

    all_values = ws.get_all_values()
    headers = all_values[0] if all_values else []
    col = {h: i for i, h in enumerate(headers)}

    row_idx = None
    for idx, row in enumerate(all_values[1:], start=2):
        m = row[col["month"]] if "month" in col and col["month"] < len(row) else ""
        if m == month:
            row_idx = idx
            break

    row_data = [month, run_id, ai_summary]
    if row_idx:
        ws.update(f"A{row_idx}", [row_data])
        print(f"  [monthly_overall] {month} 업데이트", flush=True)
    else:
        ws.append_row(row_data, value_input_option="RAW")
        print(f"  [monthly_overall] {month} 신규 추가", flush=True)
