"""
Google Sheets 읽기 모듈

읽기 대상:
  1. 마스터시트      → 갤러리 목록 (갤러리명, ID, 시트URL)
  2. 갤러리 시트     → 원본 게시글 (글번호, 제목, 본문, 날짜, 링크, 댓글수, 조회수, 추천수)
  3. Analytics 시트  → 분석 결과 (daily_issues, weekly_galleries, weekly_overall)
"""

import os
import json
from datetime import datetime, timedelta

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# 갤러리 시트 컬럼 순서 (DC-Pickaxe 고정)
_GALLERY_COLS = ["글번호", "제목", "본문", "작성자", "날짜", "링크", "댓글수", "조회수", "추천수"]


# ── 인증 ──────────────────────────────────────────────────────────────

def _client() -> gspread.Client:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        info = json.loads(raw)
        creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    else:
        path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
        creds = Credentials.from_service_account_file(path, scopes=_SCOPES)
    return gspread.authorize(creds)


# ── 마스터시트 ────────────────────────────────────────────────────────

def get_gallery_list() -> list[dict]:
    """
    마스터시트에서 갤러리 목록을 반환합니다.
    Returns: [{'gallery_name': str, 'gallery_id': str, 'sheet_url': str}, ...]
    """
    gc = _client()
    sh = gc.open_by_url(os.environ["DC_PICKAXE_MASTER_SHEET_URL"])
    rows = sh.get_worksheet(0).get_all_records()
    result = []
    for r in rows:
        name = str(r.get("갤러리명", "")).strip()
        gid  = str(r.get("갤러리ID", "")).strip()
        url  = str(r.get("저장시트 URL", "")).strip()
        if name and gid and url:
            result.append({"gallery_name": name, "gallery_id": gid, "sheet_url": url})
    return result


# ── 갤러리 시트 (원본 게시글) ──────────────────────────────────────────

def _gallery_df(sheet_url: str) -> pd.DataFrame:
    """갤러리 시트 전체를 DataFrame으로 반환 (캐시 없음 — 호출 쪽에서 관리)."""
    gc = _client()
    sh = gc.open_by_url(sheet_url)
    ws = sh.get_worksheet(0)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame(columns=_GALLERY_COLS)
    cols = _GALLERY_COLS[: len(data[0])]
    df = pd.DataFrame(data[1:], columns=cols)
    df = df[df["글번호"].astype(str).str.strip() != ""].copy()
    for c in ["댓글수", "조회수", "추천수"]:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", ""), errors="coerce"
            ).fillna(0).astype(int)
    if "날짜" in df.columns:
        df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    return df.reset_index(drop=True)


def get_posts_by_date(sheet_url: str, target_date: str) -> pd.DataFrame:
    """
    특정 날짜(YYYY-MM-DD)의 게시글만 반환합니다.
    전체 시트를 읽어 날짜 필터링 → 모든 게시글 분석 가능.
    """
    df = _gallery_df(sheet_url)
    if df.empty or "날짜" not in df.columns:
        return df
    dt = pd.to_datetime(target_date, errors="coerce")
    if pd.isna(dt):
        return df.iloc[0:0]
    return df[df["날짜"].dt.date == dt.date()].reset_index(drop=True)


def get_posts_date_range(sheet_url: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    날짜 범위(start_date ~ end_date 포함)의 게시글을 반환합니다.
    주간 분석에서 사용.
    """
    df = _gallery_df(sheet_url)
    if df.empty or "날짜" not in df.columns:
        return df
    s = pd.to_datetime(start_date, errors="coerce")
    e = pd.to_datetime(end_date, errors="coerce")
    if pd.isna(s) or pd.isna(e):
        return df.iloc[0:0]
    mask = (df["날짜"].dt.date >= s.date()) & (df["날짜"].dt.date <= e.date())
    return df[mask].reset_index(drop=True)


def get_daily_counts(sheet_url: str, target_date: str, lookback_days: int = 7) -> dict:
    """
    target_date 포함 최근 lookback_days일의 일별 게시글 수를 반환합니다.
    일간 이슈 감지의 7일 평균 계산에 사용.
    Returns: {'2026-04-13': 120, '2026-04-12': 95, ...}
    """
    df = _gallery_df(sheet_url)
    if df.empty or "날짜" not in df.columns:
        return {}
    end = pd.to_datetime(target_date, errors="coerce")
    if pd.isna(end):
        return {}
    start = end - timedelta(days=lookback_days - 1)
    mask = (df["날짜"].dt.date >= start.date()) & (df["날짜"].dt.date <= end.date())
    filtered = df[mask].copy()
    if filtered.empty:
        return {}
    counts = filtered.groupby(filtered["날짜"].dt.date).size()
    return {str(d): int(c) for d, c in counts.items()}


# ── Analytics 시트 (분석 결과) ────────────────────────────────────────

def _analytics_sheet(sheet_name: str) -> pd.DataFrame:
    gc = _client()
    sh = gc.open_by_key(os.environ["ANALYTICS_SPREADSHEET_ID"])
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame()


def get_daily_issues(n: int = 30) -> pd.DataFrame:
    """
    최신 n건의 일간 이슈 분석 결과를 반환합니다.
    has_issue=1 인 행만 포함.
    """
    df = _analytics_sheet("daily_issues")
    if df.empty:
        return df
    if "has_issue" in df.columns:
        df = df[df["has_issue"].astype(str) == "1"]
    if "date" in df.columns:
        df = df.sort_values("date", ascending=False)
    return df.head(n).reset_index(drop=True)


def get_daily_issue_dates() -> list[str]:
    """이슈가 발생한 날짜 목록 (최신순)."""
    df = _analytics_sheet("daily_issues")
    if df.empty or "date" not in df.columns:
        return []
    if "has_issue" in df.columns:
        df = df[df["has_issue"].astype(str) == "1"]
    return sorted(df["date"].unique().tolist(), reverse=True)


def get_daily_issues_by_date(target_date: str) -> pd.DataFrame:
    """특정 날짜의 이슈 분석 결과 (갤러리 전체)."""
    df = _analytics_sheet("daily_issues")
    if df.empty or "date" not in df.columns:
        return pd.DataFrame()
    return df[df["date"] == target_date].reset_index(drop=True)


def get_weekly_gallery_list() -> list[str]:
    """주간 분석이 존재하는 week_start 날짜 목록 (최신순)."""
    df = _analytics_sheet("weekly_galleries")
    if df.empty or "week_start" not in df.columns:
        return []
    return sorted(df["week_start"].unique().tolist(), reverse=True)


def get_weekly_galleries(week_start: str) -> pd.DataFrame:
    """특정 주의 갤러리별 주간 분석 결과."""
    df = _analytics_sheet("weekly_galleries")
    if df.empty or "week_start" not in df.columns:
        return pd.DataFrame()
    return df[df["week_start"] == week_start].reset_index(drop=True)


def get_weekly_overall(week_start: str) -> dict | None:
    """특정 주의 전체 종합 요약."""
    df = _analytics_sheet("weekly_overall")
    if df.empty or "week_start" not in df.columns:
        return None
    rows = df[df["week_start"] == week_start]
    if rows.empty:
        return None
    return rows.iloc[-1].to_dict()


def get_latest_weekly_info() -> dict | None:
    """가장 최근 주간 리포트의 메타 정보 (week_start, week_end)."""
    df = _analytics_sheet("weekly_overall")
    if df.empty or "week_start" not in df.columns:
        return None
    df = df.sort_values("week_start", ascending=False)
    row = df.iloc[0]
    return {"week_start": str(row.get("week_start", "")), "week_end": str(row.get("week_end", ""))}


def get_latest_daily_issue_info() -> dict | None:
    """가장 최근 일간 이슈 리포트의 메타 정보."""
    df = _analytics_sheet("daily_issues")
    if df.empty or "date" not in df.columns:
        return None
    if "has_issue" in df.columns:
        df = df[df["has_issue"].astype(str) == "1"]
    if df.empty:
        return None
    df = df.sort_values("date", ascending=False)
    row = df.iloc[0]
    count = int((df["date"] == row["date"]).sum())
    return {"date": str(row.get("date", "")), "issue_gallery_count": count}
