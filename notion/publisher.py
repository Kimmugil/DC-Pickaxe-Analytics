"""
Notion 일일 보고서 발행 모듈
- 지정한 Notion 데이터베이스에 날짜별 리포트 페이지를 생성합니다
- 100개 블록 제한(Notion API)을 고려해 청크 단위로 append
"""
import os
import json
from typing import List, Dict
from notion_client import Client


def _client() -> Client:
    return Client(auth=os.environ['NOTION_TOKEN'])


def _get_title_property_name(notion: Client, database_id: str) -> str:
    """데이터베이스의 title 속성 이름을 자동으로 찾습니다."""
    try:
        db = notion.databases.retrieve(database_id=database_id)
        for prop_name, prop_data in db['properties'].items():
            if prop_data['type'] == 'title':
                return prop_name
    except Exception:
        pass
    return '이름'  # 노션 한국어 기본값


def _get_date_property_name(notion: Client, database_id: str) -> str | None:
    """데이터베이스의 date 타입 속성 이름을 찾습니다. 없으면 None."""
    try:
        db = notion.databases.retrieve(database_id=database_id)
        for prop_name, prop_data in db['properties'].items():
            if prop_data['type'] == 'date':
                return prop_name
    except Exception:
        pass
    return None


# ─── 블록 생성 헬퍼 ────────────────────────────────────────────────

def _rich_text(content: str) -> list:
    """텍스트를 Notion rich_text 배열 형식으로 변환 (2000자 제한 처리)."""
    chunks = [content[i:i+2000] for i in range(0, max(len(content), 1), 2000)]
    return [{'type': 'text', 'text': {'content': c}} for c in chunks]


def _paragraph(content: str) -> dict:
    return {
        'object': 'block',
        'type': 'paragraph',
        'paragraph': {'rich_text': _rich_text(content)},
    }


def _heading(content: str, level: int = 2) -> dict:
    t = f'heading_{level}'
    return {
        'object': 'block',
        'type': t,
        t: {'rich_text': [{'type': 'text', 'text': {'content': content[:2000]}}]},
    }


def _callout(content: str, emoji: str = '📌') -> dict:
    return {
        'object': 'block',
        'type': 'callout',
        'callout': {
            'icon': {'type': 'emoji', 'emoji': emoji},
            'rich_text': _rich_text(content[:2000]),
        },
    }


def _divider() -> dict:
    return {'object': 'block', 'type': 'divider', 'divider': {}}


def _bulleted_item(content: str) -> dict:
    return {
        'object': 'block',
        'type': 'bulleted_list_item',
        'bulleted_list_item': {'rich_text': _rich_text(content[:2000])},
    }


def _table(rows: List[List[str]], has_header: bool = True) -> dict:
    width = max(len(r) for r in rows) if rows else 1
    table_rows = []
    for row in rows:
        cells = []
        for cell in row:
            cells.append([{'type': 'text', 'text': {'content': str(cell)[:200]}}])
        while len(cells) < width:
            cells.append([{'type': 'text', 'text': {'content': ''}}])
        table_rows.append({'type': 'table_row', 'table_row': {'cells': cells}})

    return {
        'object': 'block',
        'type': 'table',
        'table': {
            'table_width': width,
            'has_column_header': has_header,
            'has_row_header': False,
            'children': table_rows,
        },
    }


# ─── 갤러리별 블록 구성 ─────────────────────────────────────────────

def _gallery_blocks(result: dict) -> List[dict]:
    """갤러리 1개의 상세 리포트 블록 목록을 생성합니다."""
    blocks = []
    name = result.get('gallery_name', '')

    blocks.append(_heading(f"🎮 {name}", 2))
    blocks.append(_callout(
        f"신규 {result.get('new_posts_today', 0)}건 | "
        f"최근7일 {result.get('new_posts_7d', 0)}건 | "
        f"활성유저 {result.get('active_authors', 0)}명",
        emoji='📊',
    ))

    # AI 요약
    ai_summary = result.get('ai_summary', '').strip()
    if ai_summary:
        blocks.append(_heading('📝 AI 분석 요약', 3))
        for chunk in [ai_summary[i:i+1900] for i in range(0, len(ai_summary), 1900)]:
            blocks.append(_paragraph(chunk))

    # 인기글 TOP 5
    top5 = result.get('top5_posts', [])
    if isinstance(top5, str):
        try:
            top5 = json.loads(top5)
        except Exception:
            top5 = []
    if top5:
        blocks.append(_heading('🔥 인기글 TOP 5', 3))
        for i, post in enumerate(top5[:5], 1):
            line = (
                f"{i}. [{post.get('추천수', 0)}추천/{post.get('댓글수', 0)}댓글] "
                f"{post.get('제목', '')}  →  {post.get('링크', '')}"
            )
            blocks.append(_bulleted_item(line))

    # 키워드
    keywords = result.get('top_keywords', [])
    if isinstance(keywords, str):
        try:
            keywords = json.loads(keywords)
        except Exception:
            keywords = []
    if keywords:
        blocks.append(_heading('🔤 주요 키워드', 3))
        kw_text = '  ·  '.join([f"{kw}({cnt})" for kw, cnt in keywords[:15]])
        blocks.append(_paragraph(kw_text))

    # 게임 특화 신호 (비율 5% 이상만)
    game_signals = result.get('game_signals', {})
    if isinstance(game_signals, str):
        try:
            game_signals = json.loads(game_signals)
        except Exception:
            game_signals = {}
    notable = [
        f"{v.get('label', k)}: {v.get('ratio', 0)}%"
        for k, v in game_signals.items()
        if isinstance(v, dict) and v.get('ratio', 0) >= 5
    ]
    if notable:
        blocks.append(_heading('🚨 주목 신호', 3))
        for item in notable:
            blocks.append(_bulleted_item(item))

    blocks.append(_divider())
    return blocks


# ─── 메인 발행 함수 ─────────────────────────────────────────────────

def publish_daily_report(
    date: str,
    gallery_results: List[Dict],
    cross_summary: str,
) -> str:
    """
    Notion 데이터베이스에 일일 분석 보고서 페이지를 생성합니다.

    Args:
        date: 분석 기준일 (YYYY-MM-DD)
        gallery_results: 갤러리별 분석 결과 리스트
        cross_summary: 크로스 갤러리 종합 요약 문자열

    Returns:
        생성된 Notion 페이지 URL
    """
    notion = _client()
    database_id = os.environ['NOTION_DATABASE_ID']

    title = f"📊 {date} DC 키우기 갤러리 일일 리포트"

    # 데이터베이스 속성 이름 자동 탐색
    title_prop = _get_title_property_name(notion, database_id)
    date_prop  = _get_date_property_name(notion, database_id)

    # ── properties 구성 ──
    properties: dict = {
        title_prop: {'title': [{'type': 'text', 'text': {'content': title}}]},
    }
    if date_prop:
        properties[date_prop] = {'date': {'start': date}}

    # ── 블록 구성 ──
    blocks: List[dict] = []

    # 1. 종합 요약
    blocks.append(_heading('📌 오늘의 종합 요약', 1))
    for chunk in [cross_summary[i:i+1900] for i in range(0, max(len(cross_summary), 1), 1900)]:
        blocks.append(_paragraph(chunk))
    blocks.append(_divider())

    # 2. 갤러리별 현황 테이블
    blocks.append(_heading('📈 갤러리별 현황 요약', 1))
    table_rows = [['갤러리', '오늘 신규', '최근 7일', '활성유저']]
    for r in gallery_results:
        table_rows.append([
            r.get('gallery_name', ''),
            str(r.get('new_posts_today', 0)),
            str(r.get('new_posts_7d', 0)),
            str(r.get('active_authors', 0)),
        ])
    blocks.append(_table(table_rows))
    blocks.append(_divider())

    # 3. 갤러리별 상세
    blocks.append(_heading('🎮 갤러리별 상세 리포트', 1))
    for result in gallery_results:
        blocks.extend(_gallery_blocks(result))

    # ── 데이터베이스에 페이지 생성 (초기 100개 블록) ──
    page = notion.pages.create(
        parent={'database_id': database_id},
        properties=properties,
        children=blocks[:100],
    )
    page_id = page['id']

    # ── 100개 초과 블록 추가 ──
    for i in range(100, len(blocks), 100):
        notion.blocks.children.append(
            block_id=page_id,
            children=blocks[i:i + 100],
        )

    return page.get('url', f"https://notion.so/{page_id.replace('-', '')}")
