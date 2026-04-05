"""
Google Sheets 쓰기 모듈
- 분석 결과를 '분석결과', '분석대상게시글', '종합요약' 시트에 적재
- 시트 최초 실행 시 헤더 자동 생성 (ensure_sheet_headers)
"""
import os
import json
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
]

# ─── 시트별 헤더 정의 ────────────────────────────────────────────────
SHEET_HEADERS = {
    '분석결과': [
        'run_id', 'date', 'gallery_id', 'gallery_name',
        'total_posts', 'new_posts_today', 'new_posts_7d', 'active_authors',
        'top5_posts', 'top_keywords', 'hourly_dist', 'game_signals',
        'ai_summary', 'created_at',
    ],
    '분석대상게시글': [
        'run_id', 'date', 'gallery_id', 'gallery_name',
        '글번호', '제목', '본문요약', '작성자', '게시일시',
        '댓글수', '조회수', '추천수', '선택이유',
    ],
    '종합요약': [
        'run_id', 'date', 'ai_cross_summary', 'created_at',
    ],
}


def _get_client() -> gspread.Client:
    if os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'):
        info = json.loads(os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'])
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    else:
        path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', 'service_account.json')
        creds = Credentials.from_service_account_file(path, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_spreadsheet() -> gspread.Spreadsheet:
    gc = _get_client()
    return gc.open_by_key(os.environ['ANALYTICS_SPREADSHEET_ID'])


def ensure_sheet_headers():
    """
    분석 결과 스프레드시트에 필요한 시트 탭과 헤더를 자동 생성합니다.
    최초 1회만 실행하면 됩니다: python run_analysis.py --init-headers
    """
    sh = _get_spreadsheet()
    existing_titles = [ws.title for ws in sh.worksheets()]

    for sheet_name, headers in SHEET_HEADERS.items():
        if sheet_name not in existing_titles:
            ws = sh.add_worksheet(title=sheet_name, rows=5000, cols=len(headers))
            print(f"  시트 생성: '{sheet_name}'")
        else:
            ws = sh.worksheet(sheet_name)

        # 헤더가 없으면 추가
        first_row = ws.row_values(1)
        if not first_row:
            ws.append_row(headers)
            print(f"  헤더 추가: '{sheet_name}'")
        else:
            print(f"  이미 존재: '{sheet_name}'")


def save_analysis_result(result: dict):
    """갤러리별 분석 결과를 '분석결과' 시트에 한 행으로 저장합니다."""
    sh = _get_spreadsheet()
    ws = sh.worksheet('분석결과')

    row = [
        result.get('run_id', ''),
        result.get('date', ''),
        result.get('gallery_id', ''),
        result.get('gallery_name', ''),
        result.get('total_posts', 0),
        result.get('new_posts_today', 0),
        result.get('new_posts_7d', 0),
        '',  # active_authors 제거 (DC 닉네임 기반 신뢰 불가) — 컬럼 위치 보존용
        json.dumps(result.get('top5_posts', []), ensure_ascii=False),
        json.dumps(result.get('top_keywords', []), ensure_ascii=False),
        json.dumps(result.get('hourly_dist', {}), ensure_ascii=False),
        json.dumps(result.get('game_signals', {}), ensure_ascii=False),
        result.get('ai_summary', ''),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ]
    ws.append_row(row, value_input_option='USER_ENTERED')


def save_cross_gallery_summary(run_id: str, date: str, summary: str):
    """크로스 갤러리 종합 요약을 '종합요약' 시트에 저장합니다."""
    sh = _get_spreadsheet()
    ws = sh.worksheet('종합요약')
    ws.append_row([
        run_id,
        date,
        summary,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ], value_input_option='USER_ENTERED')


def save_analysis_posts(posts: list[dict], run_id: str, date: str, gallery_id: str, gallery_name: str):
    """
    분석에 사용된 게시글 목록을 '분석대상게시글' 시트에 저장합니다.
    run_id를 통해 어떤 게시글이 어느 분석 회차에 사용됐는지 추적할 수 있습니다.
    """
    if not posts:
        return

    sh = _get_spreadsheet()
    ws = sh.worksheet('분석대상게시글')

    rows = []
    for post in posts:
        body_preview = str(post.get('본문', ''))[:200].replace('\n', ' ')
        rows.append([
            run_id,
            date,
            gallery_id,
            gallery_name,
            str(post.get('글번호', '')),
            str(post.get('제목', '')),
            body_preview,
            str(post.get('작성자', '')),
            str(post.get('날짜', '')),
            int(post.get('댓글수', 0)),
            int(post.get('조회수', 0)),
            int(post.get('추천수', 0)),
            str(post.get('선택이유', '')),
        ])

    ws.append_rows(rows, value_input_option='USER_ENTERED')
