"""
DC-Pickaxe Analytics 디자인 시스템 v3
B&W — 검정/흰색/회색만 사용
"""

# ── Color tokens ─────────────────────────────────────────────────────
C_BLACK  = '#0A0A0A'
C_DARK   = '#1A1A1A'
C_MID    = '#555555'
C_LIGHT  = '#AAAAAA'
C_PALE   = '#DDDDDD'
C_BG     = '#F5F5F5'
C_CARD   = '#FFFFFF'
C_TEXT1  = '#0A0A0A'
C_TEXT2  = '#333333'
C_TEXT3  = '#888888'
C_BORDER = '#DDDDDD'

GALLERY_COLORS = [
    '#0A0A0A', '#333333', '#555555', '#777777',
    '#222222', '#444444', '#666666', '#999999',
]

CSS = """
<style>
/* ── Page ── */
[data-testid="stAppViewContainer"] > .main { background: #F5F5F5; }
section.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #FAFAFA !important; border-right: 1px solid #DDDDDD; }
[data-testid="stSidebar"] * { color: #333333 !important; }
[data-testid="stSidebar"] hr { border-color: #DDDDDD !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #F0F0F0 !important; border-color: #CCCCCC !important;
}

/* ── Card ── */
.lc {
    background: #FFFFFF;
    border: 1px solid #DDDDDD;
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 14px;
}

/* ── Stat cards ── */
.sc {
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 8px;
    background: #FFFFFF;
    border: 1px solid #DDDDDD;
}
.sc-val  { font-size: 1.7rem; font-weight: 800; color: #0A0A0A; line-height: 1.1; }
.sc-lbl  { font-size: 0.78rem; color: #555555; margin-top: 5px; display: flex; align-items: center; gap: 4px; }
.sc-sub  { font-size: 0.72rem; color: #888888; margin-top: 2px; }

/* ── Tooltip ── */
.tip-wrap { position: relative; display: inline-flex; align-items: center; cursor: help; }
.tip-icon {
    width: 14px; height: 14px; background: #AAAAAA; color: white;
    border-radius: 50%; font-size: 9px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
    margin-left: 3px; flex-shrink: 0;
}
.tip-box {
    visibility: hidden; opacity: 0;
    background: #1A1A1A; color: #F5F5F5;
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
    border: 5px solid transparent; border-top-color: #1A1A1A;
}
.tip-wrap:hover .tip-box { visibility: visible; opacity: 1; }

/* ── Section header ── */
.sec-hdr {
    font-size: 0.9rem; font-weight: 700; color: #0A0A0A;
    padding-bottom: 8px; margin-bottom: 12px;
    border-bottom: 2px solid #0A0A0A;
    display: inline-block;
}

/* ── Top post item ── */
.top-post {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 14px; margin-bottom: 6px;
    background: #F8F8F8; border-radius: 8px;
    border-left: 3px solid #333333;
}
.top-post-rank  { font-size: 1.1rem; font-weight: 800; color: #333333; min-width: 20px; }
.top-post-title { font-size: 0.88rem; font-weight: 600; color: #0A0A0A; line-height: 1.4; }
.top-post-meta  { font-size: 0.75rem; color: #555555; margin-top: 2px; }

/* ── Keyword tag ── */
.kw-tag {
    display: inline-block; margin: 2px 3px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 500;
    background: #EEEEEE; color: #1A1A1A;
    border: 1px solid #CCCCCC;
}

/* ── Calendar ── */
.cal-wrap { background: #FFFFFF; border: 1px solid #DDDDDD; border-radius: 10px; padding: 16px; margin-bottom: 14px; }
.cal-title { font-size: 0.9rem; font-weight: 700; color: #0A0A0A; margin-bottom: 10px; }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.cal-dow { text-align: center; font-size: 0.72rem; font-weight: 700; color: #888888; padding: 4px 0; }
.cal-cell {
    aspect-ratio: 1; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    border-radius: 6px; font-size: 0.82rem; color: #333333;
    min-height: 36px;
}
.cal-cell.empty { background: transparent; }
.cal-cell.has-report { background: #F0F0F0; }
.cal-cell.has-report:hover { background: #E0E0E0; }
.cal-cell.has-report a {
    text-decoration: none; color: #0A0A0A; font-weight: 600;
    display: flex; flex-direction: column; align-items: center;
    justify-content: center; width: 100%; height: 100%;
}
.cal-badge {
    font-size: 0.6rem; font-weight: 700; padding: 1px 4px;
    border-radius: 3px; margin-top: 2px; line-height: 1.4;
}
.cal-badge-d { background: #555555; color: white; }
.cal-badge-w { background: #0A0A0A; color: white; }
.cal-badge-b { background: #0A0A0A; color: white; }
.cal-today { outline: 2px solid #0A0A0A; outline-offset: -2px; }

/* ── Weekly summary card ── */
.weekly-card {
    background: #FFFFFF; border: 1px solid #DDDDDD; border-radius: 10px;
    padding: 20px 24px; margin-bottom: 14px; line-height: 1.75;
    color: #1A1A1A;
}
.weekly-card h2, .weekly-card h3 { color: #0A0A0A; margin-top: 0.8em; }

/* ── Issue badge ── */
.issue-badge {
    display: inline-block; background: #1A1A1A; color: white;
    border-radius: 4px; font-size: 0.72rem; font-weight: 700; padding: 2px 7px;
}

/* ── Signal bar ── */
.sig-bar-bg   { background: #EEEEEE; border-radius: 4px; height: 6px; width: 100%; }
.sig-bar-fill { background: #333333; border-radius: 4px; height: 6px; }
.sig-meta     { font-size: 0.76rem; color: #555555; margin-top: 4px; }
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
        f'<div class="lc" style="border-left:4px solid #0A0A0A;">'
        f'<div style="font-size:1.2rem;font-weight:800;color:#0A0A0A;">{title}</div>'
        f'<div style="font-size:0.8rem;color:#555555;margin-top:5px;'
        f'display:flex;align-items:center;gap:10px;">{meta_html}{badge_html}</div>'
        f'</div>'
    )


def cross_card(content_html: str) -> str:
    return f'<div class="weekly-card">{content_html}</div>'


def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]
