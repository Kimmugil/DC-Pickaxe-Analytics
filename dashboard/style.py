"""
DC-Pickaxe Analytics 디자인 시스템

라이트 테마 강제 + 다크모드 사용자 대응 전략:
  - .streamlit/config.toml: base="light", textColor="#0F172A"
  - 아래 CSS: 모든 텍스트 요소에 color 명시 (!important)
  - 인라인 HTML: 항상 color 속성 직접 지정 (시스템 테마 inherit 차단)

타이포그래피 참고 레퍼런스 (Sugar Labs / ShareWillow 카드 스타일):
  - label  : 0.67rem / uppercase / tracking 0.07em / #94A3B8
  - caption: 0.78rem / #64748B
  - body   : 0.88rem / line-height 1.75 / #334155
  - value  : 1.5rem+ / bold / #0F172A
  - heading: 0.95~1.1rem / semibold / #1E293B
"""

# ── 색상 상수 ─────────────────────────────────────────────────────────
C_TITLE   = "#0F172A"   # 페이지 제목, 큰 숫자
C_HEADING = "#1E293B"   # 섹션 헤더, 카드 타이틀
C_BODY    = "#334155"   # 본문 텍스트
C_MUTED   = "#64748B"   # 부연 설명, 날짜
C_LABEL   = "#94A3B8"   # uppercase 레이블
C_BORDER  = "#E2E8F0"   # 카드 테두리
C_BG      = "#F8FAFC"   # 페이지 배경
C_WHITE   = "#FFFFFF"   # 카드 배경
C_ACCENT  = "#4F46E5"   # 액센트 (링크, 활성 상태)
C_ISSUE_H = "#EF4444"   # 이슈 심각도 高
C_ISSUE_M = "#F59E0B"   # 이슈 심각도 中
C_ISSUE_L = "#64748B"   # 이슈 심각도 低/없음
C_GREEN   = "#10B981"   # 정상/양호

# 갤러리 구분색 (8색)
GALLERY_COLORS = [
    "#4F46E5", "#10B981", "#F59E0B", "#EF4444",
    "#06B6D4", "#8B5CF6", "#EC4899", "#84CC16",
]


def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]


# ── CSS 전체 ──────────────────────────────────────────────────────────
# 라이트 테마 강제 + 다크모드 사용자 대응
# - html/body/stApp 배경 명시
# - 모든 텍스트 dark color !important → 시스템 테마와 무관하게 가독 보장
_CSS = """
<style>
/* ── 라이트 테마 강제 / 다크모드 대응 ────────────────────────── */
html, body, .stApp {
    background-color: #F8FAFC !important;
    color: #0F172A !important;
}

/* ── Streamlit 자동 nav 숨김 ─────────────────────────────────── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── 사이드바 ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] * { color: #334155 !important; }
[data-testid="stSidebar"] hr { border-color: #E2E8F0 !important; }

/* ── 마크다운 텍스트 — 다크모드 대응 핵심 ───────────────────── */
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] td,
[data-testid="stMarkdownContainer"] th {
    color: #334155 !important;
    font-size: 0.88rem !important;
    line-height: 1.75 !important;
}

/* ── 헤딩 크기 제한 ──────────────────────────────────────────── */
[data-testid="stMarkdownContainer"] h1 {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.025em !important;
    line-height: 1.25 !important;
    margin-top: 0 !important;
}
[data-testid="stMarkdownContainer"] h2 {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #1E293B !important;
    letter-spacing: -0.015em !important;
    margin-top: 1rem !important;
    margin-bottom: 0.25rem !important;
}
[data-testid="stMarkdownContainer"] h3 {
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    color: #1E293B !important;
    margin-top: 0.75rem !important;
    margin-bottom: 0.2rem !important;
}
[data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] h5,
[data-testid="stMarkdownContainer"] h6 {
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    color: #334155 !important;
    margin-top: 0.5rem !important;
    margin-bottom: 0.15rem !important;
}

/* ── st.title / st.header / st.subheader ────────────────────── */
h1[data-testid="stHeading"],
.stHeading h1 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    letter-spacing: -0.03em !important;
}
h2[data-testid="stHeading"],
.stHeading h2 {
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    color: #1E293B !important;
}
h3[data-testid="stHeading"],
.stHeading h3 {
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    color: #1E293B !important;
}

/* ── 메트릭 ──────────────────────────────────────────────────── */
[data-testid="stMetricLabel"] > div {
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
}
[data-testid="stMetricValue"] > div {
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #0F172A !important;
}
[data-testid="stMetricDelta"] > div {
    font-size: 0.75rem !important;
    color: #64748B !important;
}

/* ── 캡션 ────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    font-size: 0.78rem !important;
    color: #64748B !important;
    line-height: 1.55 !important;
}

/* ── 버튼 ────────────────────────────────────────────────────── */
[data-testid="baseButton-secondary"] {
    font-size: 0.82rem !important;
    color: #334155 !important;
    border-color: #CBD5E1 !important;
    background-color: #FFFFFF !important;
}
[data-testid="baseButton-primary"] {
    font-size: 0.82rem !important;
}

/* ── 알럿 / 인포 ─────────────────────────────────────────────── */
[data-testid="stAlert"] p {
    font-size: 0.86rem !important;
    color: #1E293B !important;
    line-height: 1.65 !important;
}

/* ── 익스팬더 ────────────────────────────────────────────────── */
[data-testid="stExpander"] summary p {
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #334155 !important;
}

/* ── 셀렉트박스 / 드롭다운 ───────────────────────────────────── */
[data-testid="stSelectbox"] label p,
[data-testid="stSelectbox"] div {
    font-size: 0.85rem !important;
    color: #334155 !important;
}

/* ── 페이지링크 ──────────────────────────────────────────────── */
[data-testid="stPageLink"] a,
[data-testid="stPageLink"] a p {
    font-size: 0.85rem !important;
    color: #334155 !important;
}
[data-testid="stPageLink"]:hover a,
[data-testid="stPageLink"]:hover a p {
    color: #4F46E5 !important;
}

/* ── 구분선 ──────────────────────────────────────────────────── */
hr { border-color: #E2E8F0 !important; }

/* ── 컨테이너 내 헤딩 더 작게 (AI 요약 등) ──────────────────── */
[data-testid="stContainer"] [data-testid="stMarkdownContainer"] h2 {
    font-size: 0.95rem !important;
}
[data-testid="stContainer"] [data-testid="stMarkdownContainer"] h3,
[data-testid="stContainer"] [data-testid="stMarkdownContainer"] h4,
[data-testid="stContainer"] [data-testid="stMarkdownContainer"] h5,
[data-testid="stContainer"] [data-testid="stMarkdownContainer"] h6 {
    font-size: 0.88rem !important;
}

/* ══════════════════════════════════════════════════════════════
   PADDING FIX (v3)

   Streamlit 1.36+ emotion CSS가 !important로 container padding을
   내부적으로 고정. CSS 오버라이드 불가 → 코드 레벨에서 spacer 삽입.
   아래 CSS는 최대한 지원하되 코드 spacer가 주요 수단.
   ══════════════════════════════════════════════════════════════ */

/* 클래스/testid 양쪽 모두 시도 */
.stVerticalBlockBorderWrapper,
[data-testid="stVerticalBlockBorderWrapper"] {
    padding: 1rem 1.25rem !important;
    box-sizing: border-box !important;
}

/* 내부 컬럼의 negative margin 리셋 */
.stVerticalBlockBorderWrapper .stHorizontalBlock,
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    margin-left: 0 !important;
    margin-right: 0 !important;
}

/* expander 내용 영역 */
[data-testid="stExpander"] details > div {
    padding: 0.75rem 1rem !important;
}

/* ── 메트릭 레이블 일관성 ─────────────────────────────────────── */
[data-testid="stMetricLabel"] {
    font-size: 0.67rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #0F172A !important;
    line-height: 1.2 !important;
}
</style>
"""


def inject_css() -> None:
    """모든 페이지 최상단에서 호출. 라이트 테마 + 타이포그래피 적용."""
    import streamlit as st
    st.markdown(_CSS, unsafe_allow_html=True)


def render_sidebar_nav() -> None:
    """공통 사이드바 네비게이션."""
    import streamlit as st
    with st.sidebar:
        st.markdown(
            f'<div style="font-size:1.05rem;font-weight:700;color:{C_TITLE};padding:2px 0 4px;">'
            f'⛏️ DC-Pickaxe Analytics</div>',
            unsafe_allow_html=True,
        )
        st.caption("키우기 갤러리 동향 분석")
        st.divider()
        st.page_link("app.py",               label="🏠  홈",           use_container_width=True)
        st.page_link("pages/weekly.py",       label="📅  주간 리포트",  use_container_width=True)
        st.page_link("pages/daily.py",        label="🚨  일간 이슈",    use_container_width=True)
        st.page_link("pages/methodology.py",  label="📖  분석 방법",    use_container_width=True)
        st.divider()
        st.link_button("⛏️ 곡괭이 감시하러 가기", "https://kimmugil-dc-pickaxe-dashboard.streamlit.app/", use_container_width=True)
        st.divider()


# ── 코드 레벨 패딩 헬퍼 ─────────────────────────────────────────────

def card_spacer(px: int = 12) -> None:
    """
    st.container(border=True) 안에서 마지막 요소 뒤에 호출.
    CSS로 해결 불가능한 하단 여백을 직접 삽입.
    """
    import streamlit as st
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)


# ── HTML 컴포넌트 헬퍼 ────────────────────────────────────────────────

def label_html(text: str) -> str:
    """소형 uppercase 레이블 (카드 상단 라벨 등)."""
    return (
        f'<div style="font-size:0.67rem;font-weight:600;letter-spacing:0.07em;'
        f'text-transform:uppercase;color:{C_LABEL};margin-bottom:2px;">{text}</div>'
    )


def kw_tag_html(kw: str, cnt: int) -> str:
    """키워드 태그 필."""
    return (
        f'<span style="display:inline-block;background:#F1F5F9;border:1px solid {C_BORDER};'
        f'border-radius:6px;padding:2px 9px;font-size:0.75rem;font-weight:500;'
        f'color:{C_BODY};margin:2px 3px 2px 0;">'
        f'{kw} <span style="color:{C_LABEL};font-size:0.7rem;">{cnt}</span></span>'
    )


def issue_badge_html(score: int) -> str:
    """이슈 심각도 배지."""
    if score >= 7:
        color, label = C_ISSUE_H, f"🔴 고 · {score}점"
    elif score >= 4:
        color, label = C_ISSUE_M, f"🟡 중 · {score}점"
    else:
        color, label = C_ISSUE_L, f"⚫ 저 · {score}점"
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'background:{color}18;border:1px solid {color};border-radius:20px;'
        f'padding:3px 11px;font-size:0.78rem;font-weight:700;color:{color};'
        f'white-space:nowrap;">{label}</span>'
    )


def ai_block_html(text: str) -> str:
    """AI 요약 블록 (본문 텍스트)."""
    safe = text.replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<div style="margin-top:8px;padding:10px 14px;background:#FFFBEB;'
        f'border-left:3px solid #E8A020;border-radius:0 8px 8px 0;">'
        f'<div style="font-size:0.67rem;font-weight:700;color:#92400E;'
        f'letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">✦ AI 요약</div>'
        f'<div style="font-size:0.86rem;color:{C_BODY};line-height:1.72;">{safe}</div>'
        f'</div>'
    )


def post_row_html(rank: int, title: str, url: str, comments: int, likes: int, views: int, date_str: str) -> str:
    """TOP 게시글 한 행."""
    t = title[:38] + "…" if len(title) > 40 else title
    link = f'<a href="{url}" target="_blank" style="color:{C_ACCENT};text-decoration:none;">{t}</a>' if url else t
    return (
        f'<div style="display:flex;align-items:baseline;gap:8px;'
        f'padding:5px 0;border-bottom:1px solid {C_BORDER};">'
        f'<span style="font-size:0.7rem;font-weight:700;color:{C_LABEL};min-width:16px;">{rank}</span>'
        f'<div style="flex:1;font-size:0.84rem;color:{C_BODY};line-height:1.45;">{link}'
        f'<div style="font-size:0.73rem;color:{C_MUTED};margin-top:1px;">'
        f'💬 {comments}&nbsp; 👍 {likes}&nbsp; 👁 {views:,}&nbsp; · {date_str}</div>'
        f'</div></div>'
    )


def daily_count_bar_html(daily_counts: dict, avg: float | None = None) -> str:
    """일별 게시글 수 미니 바 차트 (HTML)."""
    if not daily_counts:
        return ""
    items = sorted(daily_counts.items())
    max_val = max(v for _, v in items) if items else 1
    max_val = max(max_val, 1)
    bars = ""
    for date_str, cnt in items:
        h   = max(4, int(cnt / max_val * 48))
        day = date_str[5:]  # MM-DD
        col = C_ACCENT
        bars += (
            f'<div style="display:flex;flex-direction:column;align-items:center;gap:2px;flex:1;">'
            f'<div style="font-size:0.6rem;color:{C_MUTED};">{cnt}</div>'
            f'<div style="width:100%;height:{h}px;background:{col};border-radius:2px 2px 0 0;min-height:4px;"></div>'
            f'<div style="font-size:0.6rem;color:{C_LABEL};">{day}</div>'
            f'</div>'
        )
    avg_line = ""
    if avg and max_val:
        avg_pct = min(100, int(avg / max_val * 100))
        avg_line = (
            f'<div style="font-size:0.7rem;color:{C_MUTED};margin-top:4px;">'
            f'7일 평균 {avg:.0f}건</div>'
        )
    return (
        f'<div style="display:flex;align-items:flex-end;gap:3px;height:72px;'
        f'padding-bottom:0;margin:4px 0 2px;">{bars}</div>{avg_line}'
    )
