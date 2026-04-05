"""
DC-Pickaxe Analytics — 종합 화면 (홈 페이지)
전체 갤러리를 아우르는 오늘의 분석 요약을 보여줍니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="DC-Pickaxe Analytics",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── 날짜 목록 캐시 (5분) ────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_available_dates() -> list[str]:
    from sheets.reader import get_available_dates
    return get_available_dates()


@st.cache_data(ttl=600)
def load_data(d: str):
    from sheets.reader import get_analysis_results, get_cross_gallery_summary
    return get_analysis_results(d), get_cross_gallery_summary(d)


# ── 사이드바 ────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⛏️ DC-Pickaxe")
    st.caption("키우기 갤러리 분석 대시보드")
    st.markdown("---")

    st.subheader("📅 리포트 날짜")

    try:
        available_dates = load_available_dates()
    except Exception:
        available_dates = []

    if available_dates:
        # 발행된 리포트 날짜 목록에서 선택
        selected_date_str = st.selectbox(
            label="날짜 선택",
            options=available_dates,
            label_visibility="collapsed",
        )
    else:
        # 아직 분석 결과가 없을 경우 날짜 직접 입력
        from datetime import date, timedelta
        _d = st.date_input(
            "날짜 선택",
            value=date.today() - timedelta(days=1),
            max_value=date.today(),
            label_visibility="collapsed",
        )
        selected_date_str = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = selected_date_str
    st.markdown("---")


# ── 메인 영역 ────────────────────────────────────────────────────────
st.title("📊 키우기 갤러리 종합 분석")
st.caption(f"기준일: **{selected_date_str}**")

try:
    results_df, cross_df = load_data(selected_date_str)
except Exception as e:
    st.error(f"데이터 로딩 오류: {e}")
    st.info("`.env` 파일 또는 Streamlit Secrets의 환경변수를 확인해주세요.")
    st.stop()

if results_df.empty:
    st.warning(f"**{selected_date_str}** 의 분석 결과가 아직 없습니다.")
    st.info("GitHub Actions가 실행된 다음날 확인하거나, 수동으로 `python run_analysis.py`를 실행해주세요.")
    st.stop()

# ── 섹션 1: 크로스 갤러리 종합 요약 ────────────────────────────────
st.subheader("🌐 오늘의 키우기 장르 종합 동향")
from dashboard.components.overview_widgets import render_cross_summary
render_cross_summary(cross_df, selected_date_str)

st.markdown("---")

# ── 섹션 2: 갤러리별 현황 카드 ──────────────────────────────────────
st.subheader("🎮 갤러리별 현황")
from dashboard.components.overview_widgets import render_gallery_cards
render_gallery_cards(results_df)

st.markdown("---")

# ── 섹션 3: 갤러리별 신규 게시글 비교 + 장르 키워드 ─────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 갤러리별 오늘 게시글 수")
    from dashboard.components.trend_charts import render_multi_gallery_trend
    render_multi_gallery_trend(results_df.to_dict('records'))

with col2:
    st.subheader("🔤 장르 전체 키워드 트렌드")
    from dashboard.components.overview_widgets import render_genre_keywords
    render_genre_keywords(results_df)

st.markdown("---")

# ── 섹션 4: 수치 요약 테이블 ────────────────────────────────────────
st.subheader("📋 갤러리별 수치 요약")
display_cols = ['gallery_name', 'new_posts_today', 'new_posts_7d', 'total_posts', 'active_authors']
col_labels = {
    'gallery_name':    '갤러리',
    'new_posts_today': '오늘 신규',
    'new_posts_7d':    '최근 7일',
    'total_posts':     '누적 게시글',
    'active_authors':  '활성 작성자',
}
available_cols = [c for c in display_cols if c in results_df.columns]
st.dataframe(
    results_df[available_cols].rename(columns=col_labels),
    use_container_width=True,
    hide_index=True,
)
