"""
Google Sheets 읽기 모듈

읽기 대상:
  1. 마스터시트      → 갤러리 목록 (갤러리명, ID, 시트URL)
  2. 갤러리 시트     → 원본 게시글 (글번호, 제목, 본문, 날짜, 링크, 댓글수, 조회수, 추천수)
  3. Analytics 시트  → 분석 결과 (daily_issues, weekly_galleries, weekly_overall)

Rate-limit 대응:
  - _client()       : 모듈 레벨 싱글턴 — 프로세스 내 1회만 인증
  - _gallery_df()   : sheet_url별 인메모리 캐시 — 같은 시트를 1회만 읽음
  - _read_with_retry: 429 발생 시 지수 백오프 재시도 (최대 5회)
"""

import os
import json
import re
import time
from datetime import datetime, timedelta

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ── DC Inside / Google Sheets 날짜 파싱 ──────────────────────────────
# DC Inside 날짜 표시 규칙:
#   당일 게시글  → "03:11"            (HH:MM, 날짜 없음)
#   당해연도 게시글 → "04.10"         (MM.DD, 연도 없음)
#   이전 연도   → "2025.04.10"        (YYYY.MM.DD)
# Google Sheets가 날짜셀을 FORMATTED_VALUE로 반환할 때 한국 로케일 형식:
#   날짜만      → "2026. 4. 10."
#   날짜+시간   → "2026. 4. 10. 오전 3:11:00" / "오후 1:19:00"

_RE_TIME_ONLY = re.compile(r"^(\d{1,2}):(\d{2})(?::\d{2})?$")
_RE_KO_DT    = re.compile(
    r"(\d{4})\.\s*(\d{1,2})\.\s*(\d{1,2})\.?"
    r"(?:\s*(오전|오후)\s*(\d{1,2}):(\d{2})(?::(\d{2}))?)?"
)
_RE_DOT_FULL = re.compile(r"^(\d{4})\.(\d{1,2})\.(\d{1,2})\.?$")
_RE_DOT_MD   = re.compile(r"^(\d{1,2})\.(\d{2})$")   # MM.DD


def _parse_dc_date(s: str) -> pd.Timestamp:
    """
    DC Inside / Google Sheets 게시글 날짜 필드 파싱.
    파싱 불가능한 값(HH:MM 시간만 등)은 pd.NaT 반환.
    """
    if not s or not str(s).strip() or str(s).lower() in ("nan", "none", ""):
        return pd.NaT
    s = str(s).strip()

    # ① ISO 표준 포맷: "2026-04-10" / "2026-04-10 03:11" → pandas 기본 처리
    result = pd.to_datetime(s, errors="coerce")
    if result is not pd.NaT and not pd.isna(result):
        return result

    # ② 한국 Google Sheets 로케일: "2026. 4. 10." / "2026. 4. 10. 오전 3:11:00"
    m = _RE_KO_DT.fullmatch(s) or _RE_KO_DT.match(s)
    if m and m.group(1):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            if m.group(4):          # 오전/오후 시각 포함
                ampm = m.group(4)
                h  = int(m.group(5))
                mi = int(m.group(6))
                sc = int(m.group(7) or 0)
                if ampm == "오후" and h < 12:
                    h += 12
                elif ampm == "오전" and h == 12:
                    h = 0
                return pd.Timestamp(year=y, month=mo, day=d, hour=h, minute=mi, second=sc)
            return pd.Timestamp(year=y, month=mo, day=d)
        except Exception:
            pass

    # ③ DC Inside 점(.) 날짜: "2026.04.10"
    m = _RE_DOT_FULL.match(s)
    if m:
        result = pd.to_datetime(f"{m.group(1)}-{m.group(2)}-{m.group(3)}", errors="coerce")
        if not pd.isna(result):
            return result

    # ④ DC Inside 월.일: "04.10" (연도는 현재 연도로 보정)
    m = _RE_DOT_MD.match(s)
    if m:
        try:
            return pd.Timestamp(
                year=datetime.now().year,
                month=int(m.group(1)),
                day=int(m.group(2)),
            )
        except Exception:
            pass

    # ⑤ HH:MM (시간만, 날짜 불명) → NaT (호출 쪽에서 ffill로 보정)
    return pd.NaT


def _parse_date_column(series: pd.Series) -> pd.Series:
    """
    날짜 컬럼 전체 파싱.
    HH:MM만 있는 당일 게시글은 인접 행 날짜로 ffill → bfill 보정.
    """
    parsed = series.apply(lambda v: _parse_dc_date(str(v)))

    if parsed.isna().any():
        # HH:MM 행 → 앞뒤 날짜로 날짜 추론 (시간은 00:00으로 대체)
        parsed = parsed.ffill().bfill()

    return parsed

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

# 갤러리 시트 컬럼 순서 (DC-Pickaxe 고정)
_GALLERY_COLS = ["글번호", "제목", "본문", "작성자", "날짜", "링크", "댓글수", "조회수", "추천수"]


# ── 인증 (싱글턴) ─────────────────────────────────────────────────────

_gc: gspread.Client | None = None


def _client() -> gspread.Client:
    """모듈 레벨 싱글턴 gspread 클라이언트. 프로세스 내 1회만 인증."""
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


# ── 429 재시도 래퍼 ──────────────────────────────────────────────────

def _read_with_retry(fn, *args, max_retries: int = 5, **kwargs):
    """
    fn(*args, **kwargs) 호출. 429(Quota Exceeded) 시 지수 백오프로 재시도.
    최대 max_retries회 시도 후에도 실패하면 예외를 올림.
    """
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except gspread.exceptions.APIError as e:
            if "429" in str(e) or "Quota" in str(e):
                wait = 2 ** attempt * 10  # 10s, 20s, 40s, 80s, 160s
                print(f"  [429] Quota exceeded — {wait}초 대기 후 재시도 ({attempt+1}/{max_retries})", flush=True)
                time.sleep(wait)
            else:
                raise
    # 마지막 시도
    return fn(*args, **kwargs)


# ── 마스터시트 ────────────────────────────────────────────────────────

def get_gallery_list() -> list[dict]:
    """
    마스터시트에서 갤러리 목록을 반환합니다.
    Returns: [{'gallery_name': str, 'gallery_id': str, 'sheet_url': str}, ...]
    """
    gc = _client()
    sh = _read_with_retry(gc.open_by_url, os.environ["DC_PICKAXE_MASTER_SHEET_URL"])
    rows = _read_with_retry(sh.get_worksheet(0).get_all_records)
    result = []
    for r in rows:
        name = str(r.get("갤러리명", "")).strip()
        gid  = str(r.get("갤러리ID", "")).strip()
        url  = str(r.get("저장시트 URL", "")).strip()
        if name and gid and url:
            result.append({"gallery_name": name, "gallery_id": gid, "sheet_url": url})
    return result


# ── 갤러리 시트 (원본 게시글) ──────────────────────────────────────────

# 프로세스 내 캐시: {sheet_url: DataFrame}
# 같은 프로세스에서 동일 URL을 여러 번 요청해도 1회만 API 호출
_df_cache: dict[str, pd.DataFrame] = {}


def clear_gallery_cache() -> None:
    """필요 시 캐시 초기화 (테스트 또는 강제 갱신용)."""
    _df_cache.clear()


def _gallery_df(sheet_url: str) -> pd.DataFrame:
    """
    갤러리 시트 전체를 DataFrame으로 반환.
    같은 프로세스 내에서 동일 URL은 1회만 읽음 (429 방지).
    """
    if sheet_url in _df_cache:
        return _df_cache[sheet_url]

    gc = _client()
    sh = _read_with_retry(gc.open_by_url, sheet_url)
    ws = sh.get_worksheet(0)
    data = _read_with_retry(ws.get_all_values)

    if not data or len(data) < 2:
        df = pd.DataFrame(columns=_GALLERY_COLS)
        _df_cache[sheet_url] = df
        return df

    cols = _GALLERY_COLS[: len(data[0])]
    df = pd.DataFrame(data[1:], columns=cols)
    df = df[df["글번호"].astype(str).str.strip() != ""].copy()
    for c in ["댓글수", "조회수", "추천수"]:
        if c in df.columns:
            df[c] = pd.to_numeric(
                df[c].astype(str).str.replace(",", ""), errors="coerce"
            ).fillna(0).astype(int)
    if "날짜" in df.columns:
        df["날짜"] = _parse_date_column(df["날짜"])
    df = df.reset_index(drop=True)
    _df_cache[sheet_url] = df
    return df


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
    sh = _read_with_retry(gc.open_by_key, os.environ["ANALYTICS_SPREADSHEET_ID"])
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    records = _read_with_retry(ws.get_all_records)
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
