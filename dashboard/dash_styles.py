"""
DC-Pickaxe Analytics 디자인 시스템 v6
Modern Clean + Bento Grid
CSS 클래스 + inline style 병용 (Streamlit 환경 호환성 보장)
"""

# ── Color tokens ─────────────────────────────────────────────────────
C_AMBER   = '#E8A020'
C_AMBER_L = '#FEF3C7'
C_BG      = '#F8FAFC'
C_CARD    = '#FFFFFF'
C_SIDEBAR = '#0F172A'
C_TEXT1   = '#0F172A'
C_TEXT2   = '#1E293B'
C_TEXT3   = '#475569'
C_TEXT4   = '#94A3B8'
C_BORDER  = '#E2E8F0'
C_RED     = '#DC2626'
C_RED_L   = '#FEF2F2'

GALLERY_COLORS = [
    '#0F172A', '#334155', '#64748B', '#94A3B8',
    '#1E293B', '#475569', '#7C8FA3', '#B0BEC5',
]

# ── CSS (Streamlit 프레임워크 요소 전용 + 클래스 보조) ──────────────
CSS = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background: #F8FAFC;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
section.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2.5rem;
}
[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong { color: #F1F5F9 !important; }
[data-testid="stSidebar"] hr { border-color: #1E293B !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #1E293B !important;
    border-color: #334155 !important;
}
[data-testid="stSidebar"] button {
    background: #1E293B !important;
    color: #CBD5E1 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
    transition: all 200ms ease;
}
[data-testid="stSidebar"] button:hover {
    background: #334155 !important;
    border-color: #E8A020 !important;
}
.top-post:hover { background: #F1F5F9 !important; }
.cal-cell.has-report:hover { background: #FDE68A; }
</style>
"""

# ── 인라인 스타일 상수 (CSS 클래스 미적용 시 폴백) ──────────────────
_S_CARD     = "background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;padding:20px 24px;margin-bottom:16px;box-shadow:0 1px 3px rgba(15,23,42,.06);"
_S_CARD_SM  = "background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;padding:16px 20px;margin-bottom:12px;box-shadow:0 1px 3px rgba(15,23,42,.05);"
_S_AMBER_L  = "border-left:5px solid #E8A020;"
_S_SEC_HDR  = "font-size:0.85rem;font-weight:700;color:#0F172A;padding-bottom:8px;margin-bottom:14px;border-bottom:2px solid #E8A020;display:inline-block;"
_S_STATUS   = "background:#F1F5F9;border:1px solid #E2E8F0;border-radius:10px;padding:8px 14px;font-size:0.78rem;color:#475569;display:flex;gap:16px;margin-bottom:16px;"


def inject_css() -> None:
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


# ── 툴팁 ─────────────────────────────────────────────────────────────
def tip(text: str) -> str:
    safe = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        '<span style="position:relative;display:inline-flex;align-items:center;cursor:help;">'
        '<span style="width:14px;height:14px;background:#94A3B8;color:white;border-radius:50%;'
        'font-size:9px;font-weight:700;display:inline-flex;align-items:center;'
        'justify-content:center;margin-left:3px;flex-shrink:0;">?</span>'
        '</span>'
    )


# ── KPI 카드 ─────────────────────────────────────────────────────────
def stat_card(label: str, value: str, sub: str = '', tint: str = 'plain', tooltip: str = '') -> str:
    tip_html = tip(tooltip) if tooltip else ''
    sub_html = (
        f'<div style="font-size:0.73rem;color:#94A3B8;margin-top:3px;">{sub}</div>'
        if sub else ''
    )
    return (
        f'<div style="{_S_CARD}">'
        f'<div style="font-size:1.85rem;font-weight:800;color:#0F172A;line-height:1.1;">{value}</div>'
        f'<div style="font-size:0.8rem;font-weight:600;color:#475569;margin-top:6px;'
        f'display:flex;align-items:center;gap:4px;">{label}{tip_html}</div>'
        f'{sub_html}'
        f'</div>'
    )


def kpi_block(label, value, sub='', tooltip='', tint='plain'):
    return stat_card(label, value, sub, tint, tooltip)


# ── 섹션 헤더 ─────────────────────────────────────────────────────────
def sec_header(title: str) -> str:
    return f'<div style="{_S_SEC_HDR}">{title}</div>'


# ── 히어로 카드 ───────────────────────────────────────────────────────
def hero_card(title: str, meta_html: str = '', badge: str = '') -> str:
    badge_html = (
        f'<span style="display:inline-block;background:#0F172A;color:white;'
        f'border-radius:6px;font-size:0.72rem;font-weight:700;padding:2px 8px;">{badge}</span>'
        if badge else ''
    )
    return (
        f'<div style="{_S_CARD}{_S_AMBER_L}">'
        f'<div style="font-size:1.2rem;font-weight:800;color:#0F172A;">{title}</div>'
        f'<div style="font-size:0.8rem;color:#475569;margin-top:5px;'
        f'display:flex;align-items:center;gap:10px;">{meta_html}{badge_html}</div>'
        f'</div>'
    )


def cross_card(content_html: str) -> str:
    return f'<div style="{_S_CARD}{_S_AMBER_L}">{content_html}</div>'


# ── 이슈 심각도 ───────────────────────────────────────────────────────
def issue_sev_class(score: int) -> str:
    if score >= 7:
        return 'sev-high'
    elif score >= 4:
        return 'sev-mid'
    return 'sev-low'


def issue_badge_class(score: int) -> str:
    if score >= 7:
        return 'sev-high-badge'
    elif score >= 4:
        return 'sev-mid-badge'
    return 'sev-low-badge'


def issue_sev_label(score: int) -> str:
    if score >= 7:
        return '고'
    elif score >= 4:
        return '중'
    return '저'


def issue_sev_color(score: int) -> str:
    """이슈 심각도별 border 색상 반환"""
    if score >= 7:
        return '#DC2626'
    elif score >= 4:
        return '#E8A020'
    return '#64748B'


def issue_sev_badge_style(score: int) -> str:
    """이슈 심각도 배지 인라인 스타일 반환"""
    if score >= 7:
        return 'background:#FEF2F2;color:#DC2626;'
    elif score >= 4:
        return 'background:#FEF3C7;color:#B45309;'
    return 'background:#F1F5F9;color:#475569;'


# ── 갤러리 컬러 ───────────────────────────────────────────────────────
def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]


# ── 키워드 태그 ───────────────────────────────────────────────────────
def kw_tag(word: str, count) -> str:
    return (
        f'<span style="display:inline-block;margin:2px 3px;padding:3px 10px;'
        f'border-radius:20px;font-size:0.8rem;font-weight:500;'
        f'background:#F1F5F9;color:#334155;border:1px solid #E2E8F0;">'
        f'{word} <b style="color:#475569">{count}</b></span>'
    )


# ── TOP 게시글 아이템 ─────────────────────────────────────────────────
def top_post_item(rank: int, title_html: str, meta: str) -> str:
    return (
        f'<div class="top-post" style="display:flex;align-items:flex-start;gap:12px;'
        f'padding:10px 14px;margin-bottom:6px;background:#F8FAFC;border-radius:10px;'
        f'border-left:3px solid #E2E8F0;">'
        f'<span style="font-size:1rem;font-weight:800;color:#E8A020;min-width:20px;">{rank}</span>'
        f'<div>'
        f'<div style="font-size:0.875rem;font-weight:600;color:#0F172A;line-height:1.45;">{title_html}</div>'
        f'<div style="font-size:0.75rem;color:#64748B;margin-top:3px;">{meta}</div>'
        f'</div></div>'
    )


# ── 분석 방법론 ───────────────────────────────────────────────────────
def _mrow(key: str, val: str) -> str:
    return (
        f'<div style="display:flex;gap:8px;font-size:0.78rem;color:#475569;margin-bottom:7px;line-height:1.6;">'
        f'<span style="font-weight:600;color:#1E293B;min-width:140px;flex-shrink:0;">{key}</span>'
        f'<span>{val}</span>'
        f'</div>'
    )


def methodology_daily_html(date_str: str) -> str:
    box = (
        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:18px 22px;">'
        f'<div style="font-size:0.85rem;font-weight:700;color:#1E293B;margin-bottom:12px;'
        f'padding-bottom:8px;border-bottom:1px solid #E2E8F0;">일간 분석 방법론</div>'
        + _mrow('분석 기준일', f'<b>{date_str}</b>')
        + _mrow('데이터 수집 범위', f'{date_str} 00:00 ~ 23:59 (24h 전체) + 최근 7일 인기글 최대 15건 (맥락 참조)')
        + _mrow('AI 분석 게시글', '최대 80건 · engagement score 내림차순 (추천수×2 + 댓글수×3 + 조회수×0.1)')
        + _mrow('TOP 5 선정 기준', 'Engagement Score = 추천수×2 + 댓글수×3 + 조회수×0.05')
        + _mrow('이슈 점수 산출', '게임신호 비율 5%↑ +1점 / 10%↑ +3점 · 1위 게시글 댓글 15↑ +1점 / 30↑ +2점 · 추천 7↑ +1점 / 15↑ +2점 · 7일 일평균 2배 초과 +2점')
        + _mrow('이슈 판정 기준', '총점 ≥ 3점 → 이슈 갤러리')
        + _mrow('이슈 심각도', '3점: 저(회색) · 4~6점: 중(황색) · 7점↑: 고(적색)')
        + _mrow('게임 신호 (9종)', '패치/업데이트·공략 수요·컨텐츠 소진·과금 민심·버그·이벤트·밸런스·신규유입·엔드게임')
        + _mrow('키워드 추출', 'kiwipiepy 형태소 분석 · 일반명사·고유명사·외래어·2자 이상·불용어 제외')
        + _mrow('AI 요약', 'Gemini 2.5 Flash · 이슈 판정 갤러리만 생성')
        + '</div>'
    )
    return box


def methodology_weekly_html(week_start: str, week_end: str) -> str:
    box = (
        f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;padding:18px 22px;">'
        f'<div style="font-size:0.85rem;font-weight:700;color:#1E293B;margin-bottom:12px;'
        f'padding-bottom:8px;border-bottom:1px solid #E2E8F0;">주간 분석 방법론</div>'
        + _mrow('분석 기간', f'<b>{week_start} (월) ~ {week_end} (일)</b> · 7일')
        + _mrow('데이터 수집 범위', '해당 기간 갤러리 시트 전체 게시글 (stats 탭 날짜별 카운트)')
        + _mrow('TOP 5 선정 기준', 'Engagement Score = 추천수×2 + 댓글수×3 + 조회수×0.05')
        + _mrow('일별 추이 정규화', '각 갤러리 일별 최대값=100 기준 상대 지수 · 갤러리 간 규모 차이 무관 활동 패턴 비교')
        + _mrow('키워드 추출', 'kiwipiepy 형태소 분석 · 일반명사·고유명사·외래어·2자 이상·불용어 제외')
        + _mrow('AI 요약', 'Gemini 2.5 Flash · 갤러리별 주간 요약 + 전체 종합 요약 2단계')
        + _mrow('최소 분석 기준', '5건 이상 게시글 갤러리만 AI 요약 생성')
        + '</div>'
    )
    return box
