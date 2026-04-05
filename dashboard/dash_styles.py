"""
DC-Pickaxe Analytics 디자인 시스템 v2
다크 사이드바 + 앰버 차트 + 틴티드 스탯카드
"""

# ── Color tokens ─────────────────────────────────────────────────────
C_AMBER   = '#FFB020'   # primary accent
C_GREEN   = '#22C55E'   # positive / trend
C_RED     = '#EF4444'   # alert
C_BLUE    = '#3B82F6'   # info
C_PURPLE  = '#A855F7'   # misc

C_BG      = '#F1F5F9'   # page background
C_CARD    = '#FFFFFF'
C_SIDEBAR = '#0F172A'   # dark sidebar

C_TEXT1   = '#0F172A'
C_TEXT2   = '#64748B'
C_TEXT3   = '#94A3B8'
C_BORDER  = '#E2E8F0'

# Tinted stat card backgrounds
TINT_AMBER  = '#FFFBEB'
TINT_GREEN  = '#F0FDF4'
TINT_BLUE   = '#EFF6FF'
TINT_PURPLE = '#FAF5FF'

GALLERY_COLORS = [
    '#FFB020', '#22C55E', '#3B82F6', '#A855F7',
    '#EF4444', '#06B6D4', '#F97316', '#84CC16',
]

CSS = """
<style>
/* ── Page & sidebar ── */
[data-testid="stAppViewContainer"] > .main { background: #F1F5F9; }
section.main .block-container { padding-top: 1.2rem; padding-bottom: 2rem; }

[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] strong {
    color: #F1F5F9 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1E293B !important; opacity: 1;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    color: #CBD5E1 !important;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #1E293B !important;
    border-color: #334155 !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 6px 8px; border-radius: 8px;
    transition: background .15s;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #1E293B !important;
}

/* ── Card ── */
.lc {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 14px;
    box-shadow: 0 1px 4px rgba(15,23,42,.06);
}

/* ── Stat cards ── */
.sc {
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 8px;
    border: 1px solid transparent;
}
.sc-amber  { background: #FFFBEB; border-color: #FDE68A; }
.sc-green  { background: #F0FDF4; border-color: #BBF7D0; }
.sc-blue   { background: #EFF6FF; border-color: #BFDBFE; }
.sc-purple { background: #FAF5FF; border-color: #DDD6FE; }
.sc-plain  { background: #FFFFFF; border-color: #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,.05); }

.sc-val  { font-size: 1.7rem; font-weight: 800; color: #0F172A; line-height: 1.1; }
.sc-lbl  { font-size: 0.78rem; color: #64748B; margin-top: 5px; display: flex; align-items: center; gap: 4px; }
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
    border-bottom: 2px solid #FFB020;
    display: inline-block;
}

/* ── Hero (gallery page header) ── */
.hero-card {
    background: white; border: 1px solid #E2E8F0;
    border-radius: 14px; padding: 18px 24px 16px;
    margin-bottom: 14px;
    border-left: 5px solid #FFB020;
    box-shadow: 0 1px 4px rgba(15,23,42,.06);
}
.hero-title { font-size: 1.4rem; font-weight: 800; color: #0F172A; line-height: 1.2; }
.hero-meta  { font-size: 0.8rem; color: #64748B; margin-top: 5px; display: flex; align-items: center; gap: 10px; }
.hero-badge {
    display: inline-block;
    background: #FFFBEB; color: #92400E;
    border: 1px solid #FDE68A;
    border-radius: 6px; font-size: 0.75rem; font-weight: 700;
    padding: 2px 8px;
}

/* ── Top post item ── */
.top-post {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 14px; margin-bottom: 6px;
    background: #F8FAFC; border-radius: 10px;
    border-left: 3px solid #FFB020;
}
.top-post-rank { font-size: 1.1rem; font-weight: 800; color: #FFB020; min-width: 20px; }
.top-post-title { font-size: 0.88rem; font-weight: 600; color: #0F172A; line-height: 1.4; }
.top-post-meta  { font-size: 0.75rem; color: #64748B; margin-top: 2px; }

/* ── Keyword tag ── */
.kw-tag {
    display: inline-block; margin: 2px 3px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 500; color: white;
}

/* ── Signal card ── */
.sig-card {
    background: white; border: 1px solid #E2E8F0;
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}
.sig-label { font-size: 0.84rem; font-weight: 600; color: #0F172A; margin-bottom: 6px; }
.sig-bar-bg { background: #F1F5F9; border-radius: 4px; height: 6px; width: 100%; }
.sig-bar-fill { border-radius: 4px; height: 6px; }
.sig-meta { font-size: 0.76rem; color: #64748B; margin-top: 5px; }

/* ── Cross-summary (AI overview) ── */
.cross-card {
    background: white; border: 1px solid #E2E8F0; border-radius: 14px;
    padding: 20px 26px; margin-bottom: 14px;
    border-left: 5px solid #22C55E;
    box-shadow: 0 1px 4px rgba(15,23,42,.06);
    line-height: 1.7;
}

/* ── Gallery nav item (sidebar) ── */
.nav-gallery {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 10px; border-radius: 8px; margin-bottom: 2px;
    cursor: default;
}
.nav-dot {
    width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0;
}
.nav-name { font-size: 0.85rem; color: #CBD5E1; flex: 1; }
.nav-cnt  { font-size: 0.75rem; color: #64748B; }

/* ── Run-id badge ── */
.run-badge {
    display: inline-block; font-family: monospace;
    font-size: 0.78rem; background: #F8FAFC;
    border: 1px solid #E2E8F0; border-radius: 4px;
    padding: 1px 7px; color: #64748B;
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
    tint: str = 'plain',   # 'amber' | 'green' | 'blue' | 'purple' | 'plain'
    tooltip: str = '',
) -> str:
    """틴티드 스탯 카드 HTML."""
    tip_html = tip(tooltip) if tooltip else ''
    sub_html = f'<div class="sc-sub">{sub}</div>' if sub else ''
    return (
        f'<div class="sc sc-{tint}">'
        f'<div class="sc-val">{value}</div>'
        f'<div class="sc-lbl">{label}{tip_html}</div>'
        f'{sub_html}'
        f'</div>'
    )


# backward compat alias
def kpi_block(label, value, sub='', tooltip='', tint='plain'):
    return stat_card(label, value, sub, tint, tooltip)


def sec_header(title: str) -> str:
    return f'<div class="sec-hdr">{title}</div>'


def hero_card(title: str, meta_html: str = '', badge: str = '') -> str:
    badge_html = f'<span class="hero-badge">{badge}</span>' if badge else ''
    return (
        f'<div class="hero-card">'
        f'<div class="hero-title">{title}</div>'
        f'<div class="hero-meta">{meta_html}{badge_html}</div>'
        f'</div>'
    )


def cross_card(content_html: str) -> str:
    return f'<div class="cross-card">{content_html}</div>'


def gallery_sidebar_item(name: str, count: int, color: str, selected: bool = False) -> str:
    bg = '#1E293B' if selected else 'transparent'
    return (
        f'<div class="nav-gallery" style="background:{bg};">'
        f'<span class="nav-dot" style="background:{color};"></span>'
        f'<span class="nav-name">{name}</span>'
        f'<span class="nav-cnt">{count:,}</span>'
        f'</div>'
    )


def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]
