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


def get_analysis_results(date: str = None) -> pd.DataFrame:
    """분석결과 시트에서 데이터를 읽습니다. date가 주어지면 해당 날짜만 반환."""
    gc = _get_client()
    sh = gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])
    ws = sh.worksheet('분석결과')
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        return df
    if date:
        df = df[df['date'] == date]
    return df.reset_index(drop=True)


def get_cross_gallery_summary(date: str = None) -> pd.DataFrame:
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
    return df.reset_index(drop=True)


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
