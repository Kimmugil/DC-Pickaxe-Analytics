"""
Google Sheets 읽기 모듈
"""
import os
import json
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly',
]


def _get_client() -> gspread.Client:
    if os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'):
        info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
        creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    return gspread.authorize(creds)


def get_gallery_list() -> list[dict]:
    gc = _get_client()
    sh = gc.open_by_url(os.environ['DC_PICKAXE_MASTER_SHEET_URL'])
    return sh.get_worksheet(0).get_all_records()


def get_gallery_stats(sheet_url: str) -> dict[str, int]:
    """
    갤러리 시트의 stats 탭에서 날짜별 게시글 수를 반환합니다.
    Returns: {'YYYY-MM-DD': count, ...}
    """
    gc = _get_client()
    sh = gc.open_by_url(sheet_url)
    try:
        ws = sh.worksheet('stats')
    except Exception:
        return {}
    rows = ws.get_all_values()
    if len(rows) < 2:
        return {}
    result: dict[str, int] = {}
    for row in rows[1:]:
        if len(row) >= 2 and row[0]:
            date_str = str(row[0]).strip()
            try:
                result[date_str] = int(row[1])
            except (ValueError, TypeError):
                result[date_str] = 0
    return result


def get_gallery_posts(sheet_url: str) -> pd.DataFrame:
    gc = _get_client()
    sh = gc.open_by_url(sheet_url)
    ws = sh.get_worksheet(0)
    data = ws.get_all_values()
    if not data or len(data) < 2:
        return pd.DataFrame()

    expected = ['글번호', '제목', '본문', '작성자', '날짜', '링크', '댓글수', '조회수', '추천수']
    cols = expected[:len(data[0])]
    df = pd.DataFrame(data[1:], columns=cols)
    df = df[df['글번호'].str.strip() != ''].dropna(subset=['글번호'])
    for c in ['댓글수', '조회수', '추천수']:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].str.replace(',', ''), errors='coerce').fillna(0).astype(int)
    if '날짜' in df.columns:
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
    return df.reset_index(drop=True)


def _analytics_sheet(name: str) -> pd.DataFrame:
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    try:
        ws = sh.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return pd.DataFrame()
    records = ws.get_all_records()
    return pd.DataFrame(records) if records else pd.DataFrame()


# ── Daily ─────────────────────────────────────────────────────────────

def get_analysis_results(date: str = None, run_id: str = None) -> pd.DataFrame:
    df = _analytics_sheet('분석결과')
    if df.empty:
        return df
    if date:
        df = df[df['date'] == date]
    if run_id:
        df = df[df['run_id'] == run_id]
    return df.reset_index(drop=True)


def get_run_ids_for_date(date: str) -> list[str]:
    df = _analytics_sheet('분석결과')
    if df.empty:
        return []
    df = df[df['date'] == date]
    seen: list[str] = []
    for rid in reversed(df['run_id'].tolist()):
        if rid and rid not in seen:
            seen.append(rid)
    return seen


def get_posts_by_run_id(run_id: str) -> pd.DataFrame:
    df = _analytics_sheet('분석대상게시글')
    if df.empty:
        return df
    return df[df['run_id'] == run_id].reset_index(drop=True)


def get_latest_overall_stats() -> dict:
    """
    가장 최근 분석 run의 전체 갤러리 합산 통계를 반환합니다.
    Returns: {new_posts_today, new_posts_7d, total_posts, date, run_id}
    """
    df = _analytics_sheet('분석결과')
    if df.empty:
        return {}
    # 가장 최신 날짜의 가장 최신 run_id
    latest_date = df['date'].max()
    date_df = df[df['date'] == latest_date]
    if 'run_id' in date_df.columns:
        latest_run = date_df['run_id'].iloc[-1]
        date_df = date_df[date_df['run_id'] == latest_run]
    for col in ['new_posts_today', 'new_posts_7d', 'total_posts']:
        if col in date_df.columns:
            date_df[col] = pd.to_numeric(date_df[col], errors='coerce').fillna(0)
    return {
        'date': latest_date,
        'run_id': date_df['run_id'].iloc[0] if 'run_id' in date_df.columns else '',
        'new_posts_today': int(date_df['new_posts_today'].sum()) if 'new_posts_today' in date_df.columns else 0,
        'new_posts_7d':    int(date_df['new_posts_7d'].sum())    if 'new_posts_7d'    in date_df.columns else 0,
        'total_posts':     int(date_df['total_posts'].sum())     if 'total_posts'     in date_df.columns else 0,
    }


def get_available_dates() -> list[str]:
    df = _analytics_sheet('분석결과')
    if df.empty:
        return []
    return sorted(df['date'].unique().tolist(), reverse=True)


def get_gallery_trend(gallery_id: str, days: int = 30) -> list[dict]:
    df = _analytics_sheet('분석결과')
    if df.empty or 'gallery_id' not in df.columns:
        return []
    gdf = df[df['gallery_id'] == gallery_id].copy()
    if gdf.empty:
        return []
    gdf['date'] = pd.to_datetime(gdf['date'], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    gdf = gdf[gdf['date'] >= cutoff].sort_values('date')
    return [{'date': str(r['date'])[:10], 'count': int(r.get('new_posts_today', 0))}
            for _, r in gdf.iterrows()]


# ── Weekly ────────────────────────────────────────────────────────────

def get_weekly_run_ids(week_start: str) -> list[str]:
    """특정 주의 run_id 목록을 최신순으로 반환합니다."""
    df = _analytics_sheet('주간종합')
    if df.empty:
        return []
    df = df[df['week_start'] == week_start]
    seen: list[str] = []
    for rid in reversed(df['run_id'].tolist()):
        if rid and rid not in seen:
            seen.append(rid)
    return seen


def get_weekly_gallery_results(week_start: str, run_id: str = None) -> pd.DataFrame:
    """특정 주의 갤러리별 주간 분석 결과를 반환합니다."""
    df = _analytics_sheet('주간분석')
    if df.empty:
        return df
    df = df[df['week_start'] == week_start]
    if run_id:
        df = df[df['run_id'] == run_id]
    elif not df.empty and 'run_id' in df.columns:
        # run_id 미지정 시 가장 최신 run_id만 사용
        latest_rid = df['run_id'].iloc[-1]
        df = df[df['run_id'] == latest_rid]
    return df.reset_index(drop=True)


def get_weekly_summary(week_start: str) -> pd.DataFrame:
    """특정 주의 종합 요약을 반환합니다."""
    df = _analytics_sheet('주간종합')
    if df.empty:
        return df
    return df[df['week_start'] == week_start].reset_index(drop=True)


def get_latest_weekly_summary() -> dict | None:
    """가장 최근 주간 종합 요약을 반환합니다."""
    df = _analytics_sheet('주간종합')
    if df.empty:
        return None
    df = df.sort_values('week_start', ascending=False)
    return df.iloc[0].to_dict()


def get_available_weekly_starts() -> list[str]:
    """주간 분석이 존재하는 week_start 날짜 목록을 최신순으로 반환합니다."""
    df = _analytics_sheet('주간종합')
    if df.empty:
        return []
    return sorted(df['week_start'].unique().tolist(), reverse=True)


# ── Calendar ──────────────────────────────────────────────────────────

def get_daily_report_index() -> list[dict]:
    """
    일간 리포트 인덱스: 날짜별 이슈 수 요약. 최신순.
    Returns: [{'date': str, 'issue_count': int, 'total_count': int, 'new_posts_today': int}, ...]
    """
    df = _analytics_sheet('분석결과')
    if df.empty:
        return []
    result = []
    for d in sorted(df['date'].unique(), reverse=True):
        ddf = df[df['date'] == d]
        if 'run_id' in ddf.columns and not ddf.empty:
            latest_run = ddf['run_id'].iloc[-1]
            ddf = ddf[ddf['run_id'] == latest_run]
        issue_count = 0
        if 'has_issue' in ddf.columns:
            issue_count = int((ddf['has_issue'].astype(str) == '1').sum())
        total_count = len(ddf)
        new_today = 0
        if 'new_posts_today' in ddf.columns:
            new_today = int(pd.to_numeric(ddf['new_posts_today'], errors='coerce').fillna(0).sum())
        result.append({
            'date': str(d),
            'issue_count': issue_count,
            'total_count': total_count,
            'new_posts_today': new_today,
        })
    return result


def get_weekly_report_index() -> list[dict]:
    """
    주간 리포트 인덱스: 주별 시작일/종료일 요약. 최신순.
    Returns: [{'week_start': str, 'week_end': str}, ...]
    """
    df = _analytics_sheet('주간종합')
    if df.empty:
        return []
    result = []
    for ws in sorted(df['week_start'].unique(), reverse=True):
        wdf = df[df['week_start'] == ws]
        latest = wdf.iloc[-1]
        result.append({
            'week_start': str(ws),
            'week_end': str(latest.get('week_end', '')),
        })
    return result


def get_calendar_data() -> dict[str, str]:
    """
    캘린더 표시용 날짜 → 리포트 타입 매핑을 반환합니다.
    Returns: {'YYYY-MM-DD': 'daily' | 'weekly' | 'both', ...}
    """
    result: dict[str, str] = {}

    # 일간: 이슈가 발생한 날짜 (has_issue=1 인 행이 하나라도 있는 날)
    daily_df = _analytics_sheet('분석결과')
    if not daily_df.empty and 'has_issue' in daily_df.columns:
        issue_df = daily_df[daily_df['has_issue'].astype(str) == '1']
        for d in issue_df['date'].unique():
            if d:
                result[d] = 'daily'
    elif not daily_df.empty:
        # has_issue 컬럼이 없는 구버전 데이터 → 날짜가 있으면 모두 표시
        for d in daily_df['date'].unique():
            if d:
                result[d] = 'daily'

    # 주간
    weekly_df = _analytics_sheet('주간종합')
    if not weekly_df.empty:
        for ws in weekly_df['week_start'].unique():
            if ws:
                if ws in result:
                    result[ws] = 'both'
                else:
                    result[ws] = 'weekly'

    return result
