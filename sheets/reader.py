"""
Google Sheets 읽기 모듈
- DC-Pickaxe 마스터 시트 및 갤러리별 시트 읽기
- 분석 결과 시트 읽기
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
    """
    DC-Pickaxe 마스터 시트에서 갤러리 목록을 반환합니다.
    마스터 시트 컬럼: 갤러리명 | 갤러리ID | 갤러리타입 | 저장시트URL | 마지막실행시각 | 결과
    """
    gc = _get_client()
    sh = gc.open_by_url(os.environ['DC_PICKAXE_MASTER_SHEET_URL'])
    ws = sh.get_worksheet(0)
    return ws.get_all_records()


def get_gallery_posts(sheet_url: str) -> pd.DataFrame:
    """
    갤러리 시트에서 게시글 데이터를 DataFrame으로 반환합니다.
    컬럼: 글번호 | 제목 | 본문 | 작성자 | 날짜 | 링크 | 댓글수 | 조회수 | 추천수
    """
    gc = _get_client()
    sh = gc.open_by_url(sheet_url)
    ws = sh.get_worksheet(0)
    data = ws.get_all_values()

    if not data or len(data) < 2:
        return pd.DataFrame()

    expected_columns = ['글번호', '제목', '본문', '작성자', '날짜', '링크', '댓글수', '조회수', '추천수']
    actual_cols = len(data[0])
    columns = expected_columns[:actual_cols]

    df = pd.DataFrame(data[1:], columns=columns)  # 헤더 행 있으면 data[1:], 없으면 data

    # 데이터 정제
    df = df[df['글번호'].str.strip() != '']
    df = df.dropna(subset=['글번호'])

    for col in ['댓글수', '조회수', '추천수']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce').fillna(0).astype(int)

    if '날짜' in df.columns:
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')

    return df.reset_index(drop=True)


def get_analysis_results(date: str = None, run_id: str = None) -> pd.DataFrame:
    """
    분석결과 시트에서 데이터를 읽습니다.
    date와 run_id 모두 주어지면 AND 조건으로 필터링합니다.
    """
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('분석결과')
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return df
    if date:
        df = df[df['date'] == date]
    if run_id:
        df = df[df['run_id'] == run_id]
    return df.reset_index(drop=True)


def get_cross_gallery_summary(date: str = None, run_id: str = None) -> pd.DataFrame:
    """종합요약 시트에서 크로스 갤러리 요약을 읽습니다."""
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('종합요약')
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return df
    if date:
        df = df[df['date'] == date]
    if run_id:
        df = df[df['run_id'] == run_id]
    return df.reset_index(drop=True)


def get_run_ids_for_date(date: str) -> list[str]:
    """
    특정 날짜에 존재하는 run_id 목록을 최신순(시트 뒤쪽 = 나중 분석)으로 반환합니다.
    """
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('분석결과')
    records = ws.get_all_records()
    if not records:
        return []
    df = pd.DataFrame(records)
    df = df[df['date'] == date]
    if df.empty:
        return []
    # 시트 순서 역순 → 가장 나중에 추가된 run_id가 앞에
    seen: list[str] = []
    for rid in reversed(df['run_id'].tolist()):
        if rid and rid not in seen:
            seen.append(rid)
    return seen


def get_posts_by_run_id(run_id: str) -> pd.DataFrame:
    """
    분석 회차 ID(run_id)로 해당 분석에 사용된 게시글 목록을 반환합니다.
    재분석 시 동일한 게시글 세트를 사용할 때 활용합니다.
    """
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('분석대상게시글')
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return df
    return df[df['run_id'] == run_id].reset_index(drop=True)


def get_available_dates() -> list[str]:
    """분석 결과가 존재하는 날짜 목록을 최신순으로 반환합니다."""
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('분석결과')
    records = ws.get_all_records()
    if not records:
        return []
    df = pd.DataFrame(records)
    return sorted(df['date'].unique().tolist(), reverse=True)


def get_gallery_trend(gallery_id: str, days: int = 30) -> list[dict]:
    """
    특정 갤러리의 최근 N일 일별 신규 게시글 수 추이를 반환합니다.

    Returns:
        [{'date': 'YYYY-MM-DD', 'count': int}, ...] 날짜 오름차순
    """
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('분석결과')
    records = ws.get_all_records()
    if not records:
        return []

    df = pd.DataFrame(records)
    if df.empty or 'gallery_id' not in df.columns:
        return []

    gdf = df[df['gallery_id'] == gallery_id].copy()
    if gdf.empty:
        return []

    # 날짜 필터
    gdf['date'] = pd.to_datetime(gdf['date'], errors='coerce')
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=days)
    gdf = gdf[gdf['date'] >= cutoff].sort_values('date')

    result = []
    for _, row in gdf.iterrows():
        result.append({
            'date':  str(row['date'])[:10],
            'count': int(row.get('new_posts_today', 0)),
        })
    return result
