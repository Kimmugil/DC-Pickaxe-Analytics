"""
Clean Line Bento 디자인 시스템
CSS 주입 + HTML 헬퍼 함수

사용법:
    from dashboard.dash_styles import inject_css, kpi_block, tip
    inject_css()
    st.markdown(kpi_block("24h 신규", "42건", tooltip="분석 기준일 당일 00:00~23:59 게시글 수"), unsafe_allow_html=True)
"""

CSS = """
<style>
/* ── Global ── */
section.main > div { padding-top: 1rem; }

/* ── Card (light card) ── */
.lc {
    background: white;
    border: 1px solid #E9ECEF;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}

/* ── Metric card ── */
.mc {
    background: white;
    border: 1px solid #E9ECEF;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
    height: 100%;
}
.mc-val {
    font-size: 1.65rem; font-weight: 700;
    color: #31333F; line-height: 1.2;
}
.mc-lbl {
    font-size: 0.8rem; color: #6C757D;
    margin-top: 5px;
    display: flex; align-items: center; gap: 4px;
}
.mc-sub { font-size: 0.73rem; color: #ADB5BD; margin-top: 2px; }

/* ── Tooltip ── */
.tip-wrap {
    position: relative; display: inline-flex;
    align-items: center; cursor: help;
}
.tip-icon {
    width: 14px; height: 14px;
    background: #CED4DA; color: white;
    border-radius: 50%; font-size: 9px; font-weight: 700;
    display: inline-flex; align-items: center; justify-content: center;
    margin-left: 3px; flex-shrink: 0; line-height: 1;
}
.tip-box {
    visibility: hidden; opacity: 0;
    background: #31333F; color: #F8F9FA;
    font-size: 0.73rem; line-height: 1.55;
    padding: 8px 11px; border-radius: 7px;
    position: absolute; bottom: 130%; left: 50%;
    transform: translateX(-50%);
    width: max-content; max-width: 230px;
    pointer-events: none;
    transition: opacity .15s ease;
    z-index: 9999; white-space: pre-line;
}
.tip-box::after {
    content: '';
    position: absolute; top: 100%; left: 50%;
    transform: translateX(-50%);
    border: 5px solid transparent;
    border-top-color: #31333F;
}
.tip-wrap:hover .tip-box { visibility: visible; opacity: 1; }

/* ── Section header ── */
.sec-hdr {
    font-size: 0.88rem; font-weight: 700; color: #31333F;
    padding-bottom: 6px; margin-bottom: 10px;
    border-bottom: 2px solid #FF4B4B;
    display: inline-block;
}

/* ── Hero card (cross-gallery summary) ── */
.hero {
    background: white;
    border: 1px solid #E9ECEF;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border-left: 4px solid #FF4B4B;
    box-shadow: 0 2px 8px rgba(255,75,75,.06);
}

/* ── Gallery summary card ── */
.gallery-card {
    background: white;
    border: 1px solid #E9ECEF;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    box-shadow: 0 1px 3px rgba(0,0,0,.04);
}
.gallery-card-name {
    font-size: 1rem; font-weight: 700; color: #31333F; margin-bottom: 6px;
}
.gallery-card-stats {
    display: flex; gap: 14px; font-size: 0.81rem;
    color: #495057; margin-bottom: 7px; flex-wrap: wrap;
}
.gallery-card-preview { font-size: 0.82rem; color: #6C757D; line-height: 1.55; }

/* ── Signal bar card ── */
.sig-card {
    background: white; border: 1px solid #E9ECEF;
    border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;
}
.sig-label { font-size: 0.84rem; font-weight: 600; color: #31333F; margin-bottom: 5px; }
.sig-bar-bg { background: #F0F2F6; border-radius: 4px; height: 6px; width: 100%; }
.sig-bar-fill { border-radius: 4px; height: 6px; }
.sig-meta { font-size: 0.77rem; color: #6C757D; margin-top: 4px; }

/* ── Keyword tag ── */
.kw-tag {
    display: inline-block; margin: 2px 3px;
    padding: 3px 10px; border-radius: 20px;
    font-size: 0.82rem; font-weight: 500; color: white;
}

/* ── Run-id badge ── */
.run-badge {
    display: inline-block; font-family: monospace;
    font-size: 0.8rem; background: #F8F9FA;
    border: 1px solid #DEE2E6; border-radius: 4px;
    padding: 1px 8px; color: #495057;
}
</style>
"""


def inject_css() -> None:
    """Streamlit 앱에 Clean Line Bento CSS를 주입합니다."""
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def tip(text: str) -> str:
    """물음표 아이콘 + 호버 툴팁 HTML 조각을 반환합니다."""
    safe = text.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
    return (
        f'<span class="tip-wrap">'
        f'<span class="tip-icon">?</span>'
        f'<span class="tip-box">{safe}</span>'
        f'</span>'
    )


def kpi_block(label: str, value: str, sub: str = '', tooltip: str = '') -> str:
    """KPI 지표 카드 HTML을 반환합니다."""
    tip_html = tip(tooltip) if tooltip else ''
    sub_html  = f'<div class="mc-sub">{sub}</div>' if sub else ''
    return (
        f'<div class="mc">'
        f'<div class="mc-val">{value}</div>'
        f'<div class="mc-lbl">{label}{tip_html}</div>'
        f'{sub_html}'
        f'</div>'
    )


def sec_header(title: str) -> str:
    """섹션 구분선 헤더 HTML을 반환합니다."""
    return f'<div class="sec-hdr">{title}</div>'


def hero_card(content: str) -> str:
    """크로스 갤러리 종합 요약용 Hero 카드 HTML을 반환합니다."""
    return f'<div class="hero">{content}</div>'


def gallery_card(name: str, new_today: int, new_7d: int, preview: str) -> str:
    """갤러리 요약 카드 HTML을 반환합니다."""
    return (
        f'<div class="gallery-card">'
        f'<div class="gallery-card-name">{name}</div>'
        f'<div class="gallery-card-stats">'
        f'<span>📝 24h <b style="color:#FF4B4B">{new_today:,}</b>건</span>'
        f'<span>📅 7일 <b>{new_7d:,}</b>건</span>'
        f'</div>'
        f'<div class="gallery-card-preview">{preview}</div>'
        f'</div>'
    )
