"""
DC-Pickaxe Analytics — 갤러리별 상세 리포트 페이지
좌측 사이드바에서 날짜와 갤러리를 선택합니다.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from datetime import date, timedelta

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='갤러리 상세 | DC-Pickaxe Analytics',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, kpi_block, sec_header, tip
inject_css()


# ── 데이터 로드 ─────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_results(d: str):
    from sheets.reader import get_analysis_results
    return get_analysis_results(d)


@st.cache_data(ttl=600)
def load_trend(gallery_id: str):
    from sheets.reader import get_gallery_trend
    return get_gallery_trend(gallery_id, days=30)


# ── 사이드바 ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('## ⛏️ DC-Pickaxe')
    st.caption('키우기 갤러리 분석 대시보드')
    st.divider()

    @st.cache_data(ttl=300)
    def _load_dates():
        from sheets.reader import get_available_dates
        return get_available_dates()

    try:
        available_dates = _load_dates()
    except Exception:
        available_dates = []

    if available_dates:
        default     = st.session_state.get('selected_date', available_dates[0])
        default_idx = available_dates.index(default) if default in available_dates else 0
        date_str    = st.selectbox('📅 날짜', options=available_dates, index=default_idx)
    else:
        _d       = st.date_input('📅 날짜', value=date.today() - timedelta(days=1), max_value=date.today())
        date_str = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = date_str
    st.divider()

    # 갤러리 목록 로드
    try:
        results_df = load_results(date_str)
    except Exception as e:
        st.error(f'데이터 로딩 오류: {e}')
        st.stop()

    if results_df.empty:
        st.warning(f'{date_str}의 데이터가 없습니다.')
        st.stop()

    gallery_names = results_df['gallery_name'].tolist()
    selected_gallery = st.radio('🎮 갤러리', options=gallery_names, label_visibility='collapsed')


# ── 선택된 갤러리 데이터 추출 ───────────────────────────────────────
row = results_df[results_df['gallery_name'] == selected_gallery]
if row.empty:
    st.warning('선택한 갤러리의 데이터를 찾을 수 없습니다.')
    st.stop()

result       = row.iloc[0].to_dict()
run_id       = result.get('run_id', '')
gallery_id   = result.get('gallery_id', '')
new_today    = int(result.get('new_posts_today', 0))
new_7d       = int(result.get('new_posts_7d', 0))
total        = int(result.get('total_posts', 0))
ai_summary   = str(result.get('ai_summary', ''))
top5_raw     = result.get('top5_posts', '[]')
keywords_raw = result.get('top_keywords', '[]')
hourly_raw   = result.get('hourly_dist', '{}')
signals_raw  = result.get('game_signals', '{}')


# ── 헤더 ────────────────────────────────────────────────────────────
st.markdown(f'## 🎮 {selected_gallery}')
st.markdown(
    f'분석 기준일 <b>{date_str}</b> &nbsp;|&nbsp; '
    f'회차 ID <span class="run-badge">{run_id}</span>',
    unsafe_allow_html=True,
)
st.markdown('')

# ── KPI 카드 ─────────────────────────────────────────────────────────
kpi_cols = st.columns(3)
with kpi_cols[0]:
    st.markdown(
        kpi_block(
            '24h 신규 게시글',
            f'{new_today:,}건',
            tooltip='분석 기준일(어제) 00:00~23:59에 작성된 게시글 수입니다.\n'
                    '이 게시글들이 AI 요약의 핵심 분석 대상입니다.',
        ),
        unsafe_allow_html=True,
    )
with kpi_cols[1]:
    st.markdown(
        kpi_block(
            '최근 7일 신규',
            f'{new_7d:,}건',
            tooltip='분석 기준일 포함 최근 7일간 작성된 게시글 수입니다.\n'
                    '5건 미만이면 AI 요약이 생성되지 않습니다.',
        ),
        unsafe_allow_html=True,
    )
with kpi_cols[2]:
    st.markdown(
        kpi_block(
            '누적 게시글',
            f'{total:,}건',
            tooltip='이 갤러리 시트에 수집된 전체 게시글 수입니다.',
        ),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── AI 분석 요약 ─────────────────────────────────────────────────────
st.markdown(sec_header('📝 AI 분석 요약'), unsafe_allow_html=True)
if ai_summary:
    st.markdown(
        f'<div class="lc">{ai_summary}</div>',
        unsafe_allow_html=True,
    )
else:
    st.caption('요약 데이터가 없습니다.')

st.markdown('')

# ── 인기글 TOP 5 + 게시글 수 추이 ───────────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.markdown(sec_header('🔥 인기글 TOP 5'), unsafe_allow_html=True)
    from dashboard.components.popular_posts_table import render_top5_table
    render_top5_table(top5_raw, gallery_name=selected_gallery)

with col_right:
    st.markdown(sec_header('📈 게시글 수 추이 (30일)'), unsafe_allow_html=True)
    if gallery_id:
        try:
            trend_data = load_trend(gallery_id)
            if trend_data:
                from dashboard.svg_charts import line, wrap
                items = [(d['date'], d['count']) for d in trend_data]
                st.markdown(wrap(line(items, height=130)), unsafe_allow_html=True)
            else:
                st.caption('아직 여러 날짜의 데이터가 없습니다.')
                st.caption('분석이 누적되면 추이 차트가 표시됩니다.')
        except Exception as e:
            st.caption(f'추이 데이터 로딩 실패: {e}')
    else:
        st.caption('갤러리 ID가 없어 추이를 불러올 수 없습니다.')

st.markdown('')

# ── 키워드 + 시간대 분포 ─────────────────────────────────────────────
col_kw, col_hourly = st.columns(2)

with col_kw:
    st.markdown(sec_header('🔤 키워드 트렌드'), unsafe_allow_html=True)
    from dashboard.components.keyword_cloud import render_keyword_tags, render_keyword_bar
    render_keyword_tags(keywords_raw)
    with st.expander('막대 차트로 보기'):
        render_keyword_bar(keywords_raw)

with col_hourly:
    st.markdown(
        sec_header('🕐 시간대별 활성도')
        + tip('분석 기준일 24h 게시글의 시간대 분포입니다. 빨간 막대가 피크 시간대입니다.'),
        unsafe_allow_html=True,
    )
    from dashboard.components.trend_charts import render_hourly_dist
    render_hourly_dist(hourly_raw)

st.markdown('')

# ── 게임 특화 신호 ────────────────────────────────────────────────────
st.markdown(
    sec_header('🎯 게임 특화 신호')
    + tip('각 신호는 관련 키워드가 포함된 게시글 비율(%)을 나타냅니다.\n5% 이상이면 주의, 10% 이상이면 경보입니다.'),
    unsafe_allow_html=True,
)

if isinstance(signals_raw, str):
    try:
        signals = json.loads(signals_raw)
    except Exception:
        signals = {}
else:
    signals = signals_raw or {}

if signals:
    sorted_signals = sorted(
        [(k, v) for k, v in signals.items() if isinstance(v, dict)],
        key=lambda x: x[1].get('ratio', 0),
        reverse=True,
    )

    sig_cols = st.columns(2)
    for i, (sig_key, sig_data) in enumerate(sorted_signals):
        label     = sig_data.get('label', sig_key)
        ratio     = sig_data.get('ratio', 0)
        pc        = sig_data.get('post_count', '-')
        bar_pct   = min(int(ratio), 100)
        bar_color = '#FF4B4B' if ratio >= 10 else ('#FFA500' if ratio >= 5 else '#ADB5BD')

        with sig_cols[i % 2]:
            st.markdown(
                f'<div class="sig-card">'
                f'<div class="sig-label">{label}</div>'
                f'<div class="sig-bar-bg">'
                f'<div class="sig-bar-fill" style="width:{bar_pct}%;background:{bar_color};"></div>'
                f'</div>'
                f'<div class="sig-meta">관련 게시글 {pc}건 &nbsp;|&nbsp; 비율 <b>{ratio}%</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
else:
    st.caption('게임 특화 지표 데이터가 없습니다.')

st.markdown('')

# ── 분석 회차 정보 ───────────────────────────────────────────────────
with st.expander(f'🔍 분석 회차 정보 (run_id: {run_id})'):
    st.markdown(f"""
**분석 회차 ID**: `{run_id}`

이 ID로 분석에 사용된 게시글 원본을 조회할 수 있습니다.

- **Google Sheets** → `분석대상게시글` 탭 → `run_id` 컬럼 필터: `{run_id}`
- **재분석 명령어**: `python run_analysis.py --rerun {run_id}`

분석 결과가 마음에 들지 않거나 재확인이 필요할 때 동일한 게시글로 다시 분석할 수 있습니다.
    """)
