"""
DC-Pickaxe Analytics 디자인 시스템 v5
Modern Clean + Bento Grid
Inter 타이포그래피 · Amber 포인트 · 다크 사이드바
"""

# ── Color tokens ─────────────────────────────────────────────────────
C_AMBER   = '#E8A020'
C_AMBER_D = '#B97A10'
C_AMBER_L = '#FEF3C7'
C_BG      = '#F8FAFC'
C_CARD    = '#FFFFFF'
C_SIDEBAR = '#0F172A'
C_TEXT1   = '#0F172A'
C_TEXT2   = '#1E293B'
C_TEXT3   = '#475569'
C_TEXT4   = '#94A3B8'
C_BORDER  = '#E2E8F0'
C_BORDER2 = '#F1F5F9'
C_RED     = '#DC2626'
C_RED_L   = '#FEF2F2'

GALLERY_COLORS = [
    '#0F172A', '#334155', '#64748B', '#94A3B8',
    '#1E293B', '#475569', '#7C8FA3', '#B0BEC5',
]

# CSS — 빈 줄(\n\n) 없이 단일 줄바꿈만 사용
CSS = """<style>
[data-testid="stAppViewContainer"] > .main { background: #F8FAFC; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
section.main .block-container { padding-top: 1rem; padding-bottom: 2.5rem; }
[data-testid="stSidebar"] { background: #0F172A !important; border-right: 1px solid #1E293B; }
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] strong { color: #F1F5F9 !important; }
[data-testid="stSidebar"] hr { border-color: #1E293B !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div { background: #1E293B !important; border-color: #334155 !important; }
[data-testid="stSidebar"] button { background: #1E293B !important; color: #CBD5E1 !important; border: 1px solid #334155 !important; border-radius: 10px !important; transition: all 200ms ease; }
[data-testid="stSidebar"] button:hover { background: #334155 !important; border-color: #E8A020 !important; }
.bento-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(15,23,42,.05), 0 2px 8px rgba(15,23,42,.04); transition: box-shadow 200ms ease; }
.bento-card:hover { box-shadow: 0 4px 16px rgba(15,23,42,.10); }
.kpi-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px 22px; margin-bottom: 8px; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.kpi-val { font-size: 1.85rem; font-weight: 800; color: #0F172A; line-height: 1.1; }
.kpi-lbl { font-size: 0.8rem; font-weight: 600; color: #475569; margin-top: 6px; display: flex; align-items: center; gap: 4px; }
.kpi-sub { font-size: 0.73rem; color: #94A3B8; margin-top: 3px; }
.issue-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px 24px; margin-bottom: 16px; border-left: 4px solid #E8A020; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.issue-card.sev-high { border-left-color: #DC2626; }
.issue-card.sev-mid  { border-left-color: #E8A020; }
.issue-card.sev-low  { border-left-color: #64748B; }
.score-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 700; }
.sev-high-badge { background: #FEF2F2; color: #DC2626; }
.sev-mid-badge  { background: #FEF3C7; color: #B45309; }
.sev-low-badge  { background: #F1F5F9; color: #475569; }
.gallery-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.sec-hdr { font-size: 0.88rem; font-weight: 700; color: #0F172A; padding-bottom: 8px; margin-bottom: 14px; border-bottom: 2px solid #E8A020; display: inline-block; }
.summary-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 22px 26px; margin-bottom: 16px; border-left: 5px solid #E8A020; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.top-post { display: flex; align-items: flex-start; gap: 12px; padding: 10px 14px; margin-bottom: 6px; background: #F8FAFC; border-radius: 10px; border-left: 3px solid #E2E8F0; transition: background 150ms ease; }
.top-post:hover { background: #F1F5F9; }
.top-post-rank  { font-size: 1rem; font-weight: 800; color: #E8A020; min-width: 20px; }
.top-post-title { font-size: 0.875rem; font-weight: 600; color: #0F172A; line-height: 1.45; }
.top-post-meta  { font-size: 0.75rem; color: #64748B; margin-top: 3px; }
.kw-tag { display: inline-block; margin: 2px 3px; padding: 3px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 500; background: #F1F5F9; color: #334155; border: 1px solid #E2E8F0; }
.cal-wrap { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 16px 18px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.cal-title { font-size: 0.9rem; font-weight: 700; color: #0F172A; margin-bottom: 10px; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.cal-dow { text-align: center; font-size: 0.7rem; font-weight: 700; color: #94A3B8; padding: 4px 0; }
.cal-cell { aspect-ratio: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; border-radius: 8px; font-size: 0.82rem; color: #475569; min-height: 34px; }
.cal-cell.empty { background: transparent; }
.cal-cell.has-report { background: #FEF3C7; }
.cal-cell.has-report:hover { background: #FDE68A; }
.cal-cell.has-report a { text-decoration: none; color: #0F172A; font-weight: 700; display: flex; flex-direction: column; align-items: center; justify-content: center; width: 100%; height: 100%; }
.cal-badge { font-size: 0.58rem; font-weight: 700; padding: 1px 4px; border-radius: 4px; margin-top: 2px; line-height: 1.4; }
.cal-badge-d { background: #475569; color: white; }
.cal-badge-w { background: #E8A020; color: white; }
.cal-badge-b { background: #E8A020; color: white; }
.cal-today { outline: 2px solid #E8A020; outline-offset: -2px; border-radius: 8px; }
.method-box { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px 20px; }
.method-section-title { font-size: 0.82rem; font-weight: 700; color: #1E293B; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #E2E8F0; }
.method-row { display: flex; gap: 8px; font-size: 0.78rem; color: #475569; margin-bottom: 6px; line-height: 1.6; }
.method-key { font-weight: 600; color: #1E293B; min-width: 130px; flex-shrink: 0; }
.method-val { color: #475569; }
.alert-banner { border-radius: 12px; padding: 12px 16px; margin-bottom: 14px; display: flex; align-items: center; gap: 10px; font-size: 0.85rem; font-weight: 600; }
.alert-issue { background: #FEF3C7; border: 1px solid #F59E0B; color: #92400E; }
.alert-clear { background: #F0FDF4; border: 1px solid #86EFAC; color: #166534; }
.status-bar { background: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px 14px; font-size: 0.78rem; color: #475569; display: flex; gap: 16px; margin-bottom: 16px; }
.status-bar b { color: #1E293B; }
.tip-wrap { position: relative; display: inline-flex; align-items: center; cursor: help; }
.tip-icon { width: 14px; height: 14px; background: #94A3B8; color: white; border-radius: 50%; font-size: 9px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; margin-left: 3px; flex-shrink: 0; }
.tip-box { visibility: hidden; opacity: 0; background: #0F172A; color: #F1F5F9; font-size: 0.72rem; line-height: 1.55; padding: 8px 11px; border-radius: 10px; position: absolute; bottom: 130%; left: 50%; transform: translateX(-50%); width: max-content; max-width: 240px; pointer-events: none; transition: opacity .15s ease; z-index: 9999; white-space: pre-line; }
.tip-box::after { content: ''; position: absolute; top: 100%; left: 50%; transform: translateX(-50%); border: 5px solid transparent; border-top-color: #0F172A; }
.tip-wrap:hover .tip-box { visibility: visible; opacity: 1; }
.lc { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 22px; margin-bottom: 14px; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.sc { border-radius: 16px; padding: 16px 18px; margin-bottom: 8px; background: #FFFFFF; border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.sc-val { font-size: 1.7rem; font-weight: 800; color: #0F172A; line-height: 1.1; }
.sc-lbl { font-size: 0.78rem; color: #475569; margin-top: 5px; display: flex; align-items: center; gap: 4px; }
.sc-sub { font-size: 0.72rem; color: #94A3B8; margin-top: 2px; }
.issue-badge { display: inline-block; background: #0F172A; color: white; border-radius: 6px; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; }
.weekly-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px 24px; margin-bottom: 14px; border-left: 4px solid #E8A020; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
.hero-card { background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 18px 24px; margin-bottom: 14px; border-left: 5px solid #E8A020; box-shadow: 0 1px 3px rgba(15,23,42,.05); }
</style>"""


def inject_css() -> None:
    import streamlit as st
    # Google Fonts: <link> 방식이 동적 주입 환경에서 더 안정적
    st.markdown(
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(CSS, unsafe_allow_html=True)


# ── Helper: tooltip ──────────────────────────────────────────────────
def tip(text: str) -> str:
    safe = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        '<span class="tip-wrap">'
        '<span class="tip-icon">?</span>'
        f'<span class="tip-box">{safe}</span>'
        '</span>'
    )


# ── Helper: KPI card ─────────────────────────────────────────────────
def stat_card(
    label: str,
    value: str,
    sub: str = '',
    tint: str = 'plain',
    tooltip: str = '',
) -> str:
    tip_html = tip(tooltip) if tooltip else ''
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ''
    return (
        '<div class="kpi-card">'
        f'<div class="kpi-val">{value}</div>'
        f'<div class="kpi-lbl">{label}{tip_html}</div>'
        f'{sub_html}'
        '</div>'
    )


# ── Helper: kpi_block (legacy alias) ────────────────────────────────
def kpi_block(label, value, sub='', tooltip='', tint='plain'):
    return stat_card(label, value, sub, tint, tooltip)


# ── Helper: section header ───────────────────────────────────────────
def sec_header(title: str) -> str:
    return f'<div class="sec-hdr">{title}</div>'


# ── Helper: hero card ────────────────────────────────────────────────
def hero_card(title: str, meta_html: str = '', badge: str = '') -> str:
    badge_html = f'<span class="issue-badge">{badge}</span>' if badge else ''
    return (
        '<div class="hero-card">'
        f'<div style="font-size:1.2rem;font-weight:800;color:#0F172A;">{title}</div>'
        '<div style="font-size:0.8rem;color:#475569;margin-top:5px;'
        f'display:flex;align-items:center;gap:10px;">{meta_html}{badge_html}</div>'
        '</div>'
    )


# ── Helper: cross card (legacy alias) ────────────────────────────────
def cross_card(content_html: str) -> str:
    return f'<div class="weekly-card">{content_html}</div>'


# ── Helper: issue severity ───────────────────────────────────────────
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


# ── Helper: gallery color ─────────────────────────────────────────────
def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]


# ── Helper: methodology rows HTML ────────────────────────────────────
def _mrow(key: str, val: str) -> str:
    return (
        '<div class="method-row">'
        f'<span class="method-key">{key}</span>'
        f'<span class="method-val">{val}</span>'
        '</div>'
    )


def methodology_daily_html(date_str: str) -> str:
    """일간 분석 방법론 HTML 블록을 반환합니다."""
    return (
        '<div class="method-box">'
        '<div class="method-section-title">일간 분석 방법론</div>'
        + _mrow('분석 기준일', f'<b>{date_str}</b>')
        + _mrow('데이터 수집 범위', f'{date_str} 00:00 ~ 23:59 (24시간) + 최근 7일 인기글 최대 15건 (맥락 참조)')
        + _mrow('AI 분석 게시글', '최대 80건 (24h 전체 + 7일 인기글, engagement score 내림차순)')
        + _mrow('Engagement Score', '추천수×2 + 댓글수×3 + 조회수×0.05 (TOP 5 선정 기준)')
        + _mrow('이슈 점수 산출', '게임신호 비율 5%↑: +1점, 10%↑: +3점 / 1위 게시글 댓글 15↑: +1점, 30↑: +2점 / 추천 7↑: +1점, 15↑: +2점 / 7일 일평균 대비 2배 초과: +2점')
        + _mrow('이슈 판정 기준', '총 이슈 점수 ≥ 3점 → 이슈 갤러리 판정')
        + _mrow('이슈 심각도', '점수 3: 저(회색) / 4~6: 중(황색) / 7↑: 고(적색)')
        + _mrow('게임 신호 분석', '패치/업데이트 반응·공략 수요·컨텐츠 소진·과금 민심·버그·이벤트·밸런스·신규유입·엔드게임 등 9개 신호 키워드 패턴 매칭')
        + _mrow('키워드 추출', 'kiwipiepy 한국어 형태소 분석 (일반명사·고유명사·외래어, 2자 이상, 불용어 제외)')
        + _mrow('AI 요약 생성', 'Gemini 2.5 Flash — 이슈 판정 갤러리에 한해 생성 (비용 절감)')
        + '</div>'
    )


def methodology_weekly_html(week_start: str, week_end: str) -> str:
    """주간 분석 방법론 HTML 블록을 반환합니다."""
    return (
        '<div class="method-box">'
        '<div class="method-section-title">주간 분석 방법론</div>'
        + _mrow('분석 기간', f'<b>{week_start} (월) ~ {week_end} (일)</b>, 총 7일')
        + _mrow('데이터 수집 범위', '해당 기간 갤러리 시트의 전체 게시글 (stats 탭 날짜별 카운트 기준)')
        + _mrow('Engagement Score', '추천수×2 + 댓글수×3 + 조회수×0.05 → 주간 TOP 5 게시글 선정')
        + _mrow('일별 추이 정규화', '각 갤러리의 일별 최대값=100 기준 상대 지수 — 갤러리 간 절대치 차이 무관하게 활동 패턴 비교')
        + _mrow('키워드 추출', 'kiwipiepy 한국어 형태소 분석 (일반명사·고유명사·외래어, 2자 이상, 불용어 제외)')
        + _mrow('AI 요약 생성', 'Gemini 2.5 Flash — 갤러리별 주간 요약 + 전체 종합 요약 2단계 생성')
        + _mrow('최소 분석 기준', '5건 이상 게시글이 있는 갤러리만 AI 요약 생성')
        + '</div>'
    )
