"""
DC-Pickaxe Analytics 디자인 시스템 v4
다크 사이드바 + 앰버 포인트 + 화이트 카드
"""

# ── Color tokens ─────────────────────────────────────────────────────
C_AMBER   = '#E8A020'
C_BG      = '#F0F2F6'
C_CARD    = '#FFFFFF'
C_SIDEBAR = '#0F172A'
C_TEXT1   = '#0F172A'
C_TEXT2   = '#475569'
C_TEXT3   = '#94A3B8'
C_BORDER  = '#E2E8F0'

GALLERY_COLORS = [
    '#0F172A', '#334155', '#64748B', '#94A3B8',
    '#1E293B', '#475569', '#7C8FA3', '#B0BEC5',
]

CSS = """
<style>
/* ── Page ── */
[data-testid="stAppViewContainer"] > .main { background: #F0F2F6; }
section.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] strong {
    color: #F1F5F9 !important;
}
[data-testid="stSidebar"] hr { border-color: #1E293B !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #1E293B !important; border-color: #334155 !important;
}
[data-testid="stSidebar"] button {
    background: #1E293B !important; color: #CBD5E1 !important;
    border: 1px solid #334155 !important;
}
[data-testid="stSidebar"] button:hover {
    background: #334155 !important; border-color: #E8A020 !important;
}

/* ── Card ── */
.lc {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
}

/* ── Stat cards ── */
.sc {
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 8px;
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
}
.sc-val  { font-size: 1.7rem; font-weight: 800; color: #0F172A; line-height: 1.1; }
.sc-lbl  { font-size: 0.78rem; color: #475569; margin-top: 5px;
           display: flex; align-items: center; gap: 4px; }
.sc-sub  { font-size: 0.72rem; color: #94A3B8; margin-top: 2px; }

/* ── Tooltip ── */
.tip-wrap { position: relative; display: inline-flex; align-items: center; cursor: help; }
.tip-icon {
    width: 14px; height: 14px; background: #94A3B8; color: white;
    border-radius: 50%; font-size: 9px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
    margin-left: 3px; flex-shrink: 0;
}
.tip-box {
    visibility: hidden; opacity: 0;
    background: #0F172A; color: #F1F5F9;
    font-size: 0.72rem; line-height: 1.55;
    padding: 8px 11px; border-radius: 8px;
    position: absolute; bottom: 130%; left: 50%;
    transform: translateX(-50%);
    width: max-content; max-width: 240px;
    pointer-events: none;
    transition: opacity .15s ease;
    z-index: 9999; white-space: pre-line;
}
.tip-box::after {
    content: ''; position: absolute; top: 100%; left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent; border-top-color: #0F172A;
}
.tip-wrap:hover .tip-box { visibility: visible; opacity: 1; }

/* ── Section header ── */
.sec-hdr {
    font-size: 0.9rem; font-weight: 700; color: #0F172A;
    padding-bottom: 8px; margin-bottom: 12px;
    border-bottom: 2px solid #E8A020;
    display: inline-block;
}

/* ── Top post item ── */
.top-post {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 14px; margin-bottom: 6px;
    background: #F8FAFC; border-radius: 10px;
    border-left: 3px solid #E8A020;
}
.top-post-rank  { font-size: 1.1rem; font-weight: 800; color: #E8A020; min-width: 20px; }
.top-post-title { font-size: 0.88rem; font-weight: 600; color: #0F172A; line-height: 1.4; }
.top-post-meta  { font-size: 0.75rem; color: #64748B; margin-top: 2px; }

/* ── Keyword tag ── */
.kw-tag {
    display: inline-block; margin: 2px 3px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 500;
    background: #F1F5F9; color: #334155;
    border: 1px solid #E2E8F0;
}

/* ── Calendar ── */
.cal-wrap {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 16px; margin-bottom: 14px;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
}
.cal-title { font-size: 0.9rem; font-weight: 700; color: #0F172A; margin-bottom: 10px; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.cal-dow { text-align: center; font-size: 0.72rem; font-weight: 700; color: #94A3B8; padding: 4px 0; }
.cal-cell {
    aspect-ratio: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    border-radius: 6px; font-size: 0.82rem; color: #475569;
    min-height: 36px;
}
.cal-cell.empty { background: transparent; }
.cal-cell.has-report { background: #FFF8ED; }
.cal-cell.has-report:hover { background: #FEF3C7; }
.cal-cell.has-report a {
    text-decoration: none; color: #0F172A; font-weight: 600;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    width: 100%; height: 100%;
}
.cal-badge {
    font-size: 0.6rem; font-weight: 700; padding: 1px 4px;
    border-radius: 3px; margin-top: 2px; line-height: 1.4;
}
.cal-badge-d { background: #475569; color: white; }
.cal-badge-w { background: #E8A020; color: white; }
.cal-badge-b { background: #E8A020; color: white; }
.cal-today { outline: 2px solid #E8A020; outline-offset: -2px; }

/* ── Weekly summary card ── */
.weekly-card {
    background: #FFFFFF; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 14px;
    border-left: 4px solid #E8A020;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
}

/* ── Issue badge ── */
.issue-badge {
    display: inline-block; background: #0F172A; color: white;
    border-radius: 4px; font-size: 0.72rem; font-weight: 700;
    padding: 2px 7px;
}

/* ── Hero card ── */
.hero-card {
    background: white; border: 1px solid #E2E8F0;
    border-radius: 12px; padding: 18px 24px;
    margin-bottom: 14px;
    border-left: 5px solid #E8A020;
    box-shadow: 0 1px 3px rgba(15,23,42,.06);
}
</style>
"""


def inject_css() -> None:
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def tip(text: str) -> str:
    safe = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        f'<span class="tip-wrap">'
        f'<span class="tip-icon">?</span>'
        f'<span class="tip-box">{safe}</span>'
        f'</span>'
    )


def stat_card(
    label: str,
    value: str,
    sub: str = '',
    tint: str = 'plain',
    tooltip: str = '',
) -> str:
    tip_html = tip(tooltip) if tooltip else ''
    sub_html = f'<div class="sc-sub">{sub}</div>' if sub else ''
    return (
        f'<div class="sc">'
        f'<div class="sc-val">{value}</div>'
        f'<div class="sc-lbl">{label}{tip_html}</div>'
        f'{sub_html}'
        f'</div>'
    )


def kpi_block(label, value, sub='', tooltip='', tint='plain'):
    return stat_card(label, value, sub, tint, tooltip)


def sec_header(title: str) -> str:
    return f'<div class="sec-hdr">{title}</div>'


def hero_card(title: str, meta_html: str = '', badge: str = '') -> str:
    badge_html = f'<span class="issue-badge">{badge}</span>' if badge else ''
    return (
        f'<div class="hero-card">'
        f'<div style="font-size:1.2rem;font-weight:800;color:#0F172A;">{title}</div>'
        f'<div style="font-size:0.8rem;color:#475569;margin-top:5px;'
        f'display:flex;align-items:center;gap:10px;">{meta_html}{badge_html}</div>'
        f'</div>'
    )


def cross_card(content_html: str) -> str:
    return f'<div class="weekly-card">{content_html}</div>'


def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]
