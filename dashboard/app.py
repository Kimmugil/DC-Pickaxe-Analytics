"""
DC-Pickaxe Analytics — 종합 화면 (홈 페이지)
전체 갤러리를 아우르는 분석 요약을 보여줍니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='DC-Pickaxe Analytics',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, kpi_block, sec_header, tip
inject_css()


# ── 데이터 로드 (캐시) ────────────────────────────────────────────────
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
    st.markdown('## ⛏️ DC-Pickaxe')
    st.caption('키우기 갤러리 분석 대시보드')
    st.divider()

    try:
        available_dates = load_available_dates()
    except Exception:
        available_dates = []

    if available_dates:
        selected_date_str = st.selectbox(
            '📅 리포트 날짜',
            options=available_dates,
        )
    else:
        from datetime import date, timedelta
        _d = st.date_input(
            '📅 리포트 날짜',
            value=date.today() - timedelta(days=1),
            max_value=date.today(),
        )
        selected_date_str = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = selected_date_str
    st.divider()
    st.caption('갤러리별 상세 분석은\n**갤러리 상세** 페이지에서 확인하세요.')


# ── 데이터 로드 ──────────────────────────────────────────────────────
try:
    results_df, cross_df = load_data(selected_date_str)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.info('`.env` 파일 또는 Streamlit Secrets의 환경변수를 확인해주세요.')
    st.stop()

if results_df.empty:
    st.warning(f'**{selected_date_str}** 의 분석 결과가 아직 없습니다.')
    st.info('GitHub Actions 실행 후 또는 `python run_analysis.py` 를 먼저 실행해주세요.')
    st.stop()

# ── 헤더 ─────────────────────────────────────────────────────────────
st.markdown('## 📊 키우기 갤러리 종합 분석')
st.markdown(
    f'분석 기준일 <b>{selected_date_str}</b> &nbsp;|&nbsp; '
    f'갤러리 <b>{len(results_df)}</b>개',
    unsafe_allow_html=True,
)
st.markdown('')

# ── 섹션 1: KPI 요약 ─────────────────────────────────────────────────
total_24h = int(results_df['new_posts_today'].sum()) if 'new_posts_today' in results_df.columns else 0
total_7d  = int(results_df['new_posts_7d'].sum())    if 'new_posts_7d'    in results_df.columns else 0
total_cum = int(results_df['total_posts'].sum())     if 'total_posts'     in results_df.columns else 0

kpi_cols = st.columns(3)
with kpi_cols[0]:
    st.markdown(
        kpi_block(
            '24h 전체 신규',
            f'{total_24h:,}건',
            tooltip='분석 기준일(어제) 00:00~23:59에 작성된 게시글의 전체 갤러리 합산 수입니다.',
        ),
        unsafe_allow_html=True,
    )
with kpi_cols[1]:
    st.markdown(
        kpi_block(
            '7일 전체 신규',
            f'{total_7d:,}건',
            tooltip='분석 기준일 포함 최근 7일간 작성된 게시글의 전체 갤러리 합산 수입니다.',
        ),
        unsafe_allow_html=True,
    )
with kpi_cols[2]:
    st.markdown(
        kpi_block(
            '누적 게시글 (전체)',
            f'{total_cum:,}건',
            tooltip='수집된 전체 게시글 수의 갤러리 합산값입니다. 갤러리 시트에 쌓인 전체 데이터 기준입니다.',
        ),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── 섹션 2: 크로스 갤러리 종합 요약 ────────────────────────────────
st.markdown(sec_header('🌐 오늘의 키우기 장르 종합 동향'), unsafe_allow_html=True)
from dashboard.components.overview_widgets import render_cross_summary
render_cross_summary(cross_df, selected_date_str)

st.markdown('')

# ── 섹션 3: 갤러리별 현황 카드 ──────────────────────────────────────
st.markdown(sec_header('🎮 갤러리별 현황'), unsafe_allow_html=True)
from dashboard.components.overview_widgets import render_gallery_cards
render_gallery_cards(results_df)

st.markdown('')

# ── 섹션 4: 갤러리별 게시글 비교 + 장르 키워드 ──────────────────────
col_chart, col_kw = st.columns(2)

with col_chart:
    st.markdown(sec_header('📈 갤러리별 24h 신규'), unsafe_allow_html=True)
    from dashboard.components.trend_charts import render_multi_gallery_trend
    render_multi_gallery_trend(results_df.to_dict('records'))

with col_kw:
    st.markdown(sec_header('🔤 장르 전체 키워드'), unsafe_allow_html=True)
    from dashboard.components.overview_widgets import render_genre_keywords
    render_genre_keywords(results_df)

st.markdown('')

# ── 섹션 5: 수치 요약 테이블 ────────────────────────────────────────
st.markdown(sec_header('📋 갤러리별 수치 요약'), unsafe_allow_html=True)

display_cols = ['gallery_name', 'new_posts_today', 'new_posts_7d', 'total_posts']
col_labels = {
    'gallery_name':    '갤러리',
    'new_posts_today': '24h 신규',
    'new_posts_7d':    '최근 7일',
    'total_posts':     '누적 게시글',
}
available_cols = [c for c in display_cols if c in results_df.columns]
st.dataframe(
    results_df[available_cols].rename(columns=col_labels),
    use_container_width=True,
    hide_index=True,
)
