"""
DC-Pickaxe Analytics — 갤러리별 상세 리포트 페이지
좌측 사이드바에서 날짜와 갤러리를 선택하면 해당 상세 분석을 확인할 수 있습니다.
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
    page_title="갤러리 상세 | DC-Pickaxe Analytics",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 데이터 로드 ─────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_results(d: str):
    from sheets.reader import get_analysis_results
    return get_analysis_results(d)


# ── 사이드바 ────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⛏️ DC-Pickaxe")
    st.caption("키우기 갤러리 분석 대시보드")
    st.markdown("---")

    st.subheader("📅 리포트 날짜")

    @st.cache_data(ttl=300)
    def _load_dates():
        from sheets.reader import get_available_dates
        return get_available_dates()

    try:
        available_dates = _load_dates()
    except Exception:
        available_dates = []

    if available_dates:
        default = st.session_state.get('selected_date', available_dates[0])
        default_idx = available_dates.index(default) if default in available_dates else 0
        date_str = st.selectbox(
            "날짜 선택",
            options=available_dates,
            index=default_idx,
            label_visibility="collapsed",
        )
    else:
        _d = st.date_input(
            "날짜 선택",
            value=date.today() - timedelta(days=1),
            max_value=date.today(),
            label_visibility="collapsed",
        )
        date_str = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = date_str

    st.markdown("---")

    # 갤러리 목록 로드
    try:
        results_df = load_results(date_str)
    except Exception as e:
        st.error(f"데이터 로딩 오류: {e}")
        st.stop()

    if results_df.empty:
        st.warning(f"{date_str}의 데이터가 없습니다.")
        st.stop()

    gallery_names = results_df['gallery_name'].tolist()
    st.subheader("🎮 갤러리 선택")
    selected_gallery = st.radio(
        label="갤러리",
        options=gallery_names,
        label_visibility="collapsed",
        key="gallery_selector",
    )

# ── 선택된 갤러리 데이터 추출 ───────────────────────────────────────
row = results_df[results_df['gallery_name'] == selected_gallery]
if row.empty:
    st.warning("선택한 갤러리의 데이터를 찾을 수 없습니다.")
    st.stop()

result = row.iloc[0].to_dict()

run_id       = result.get('run_id', '')
new_today    = int(result.get('new_posts_today', 0))
new_7d       = int(result.get('new_posts_7d', 0))
total        = int(result.get('total_posts', 0))
active       = int(result.get('active_authors', 0))
ai_summary   = str(result.get('ai_summary', ''))
top5_raw     = result.get('top5_posts', '[]')
keywords_raw = result.get('top_keywords', '[]')
hourly_raw   = result.get('hourly_dist', '{}')
signals_raw  = result.get('game_signals', '{}')

# ── 헤더 ────────────────────────────────────────────────────────────
st.title(f"🎮 {selected_gallery}")
st.caption(f"분석 기준일: **{date_str}**  |  분석 회차 ID: `{run_id}`")

# 핵심 지표
m1, m2, m3, m4 = st.columns(4)
m1.metric("오늘 신규", f"{new_today:,}건")
m2.metric("최근 7일", f"{new_7d:,}건")
m3.metric("누적 게시글", f"{total:,}건")
m4.metric("활성 작성자", f"{active:,}명")

st.markdown("---")

# ── AI 분석 요약 ─────────────────────────────────────────────────────
st.subheader("📝 AI 분석 요약")
if ai_summary:
    st.markdown(ai_summary)
else:
    st.caption("요약 데이터가 없습니다.")

st.markdown("---")

# ── 인기글 TOP 5 + 게시글 추이 ──────────────────────────────────────
col_left, col_right = st.columns([1.2, 1])

with col_left:
    st.subheader("🔥 인기글 TOP 5")
    from dashboard.components.popular_posts_table import render_top5_table
    render_top5_table(top5_raw, gallery_name=selected_gallery)

with col_right:
    st.subheader("📈 게시글 수 추이 (30일)")
    from dashboard.components.trend_charts import render_daily_trend
    # daily_trend는 분석결과에 없으므로 hourly_dist로 대체 안내
    daily_trend_data = result.get('daily_trend', [])
    if isinstance(daily_trend_data, str):
        try:
            daily_trend_data = json.loads(daily_trend_data)
        except Exception:
            daily_trend_data = []
    if daily_trend_data:
        render_daily_trend({'daily_trend': daily_trend_data})
    else:
        st.caption("추이 데이터는 대시보드 다음 버전에서 제공될 예정입니다.")
        st.caption("(현재는 일별 raw 데이터를 Sheets에서 직접 읽는 방식으로 추가할 수 있습니다.)")

st.markdown("---")

# ── 키워드 + 시간대 분포 ─────────────────────────────────────────────
col_kw, col_hourly = st.columns(2)

with col_kw:
    st.subheader("🔤 키워드 트렌드")
    from dashboard.components.keyword_cloud import render_keyword_tags, render_keyword_bar
    render_keyword_tags(keywords_raw)
    with st.expander("막대 차트로 보기"):
        render_keyword_bar(keywords_raw)

with col_hourly:
    st.subheader("🕐 시간대별 활성도")
    from dashboard.components.trend_charts import render_hourly_dist
    render_hourly_dist(hourly_raw)

st.markdown("---")

# ── 키우기 게임 특화 지표 ─────────────────────────────────────────────
st.subheader("🎯 게임 특화 신호")

if isinstance(signals_raw, str):
    try:
        signals = json.loads(signals_raw)
    except Exception:
        signals = {}
else:
    signals = signals_raw or {}

if signals:
    # 신호를 비율 기준 내림차순 정렬 후 표시
    sorted_signals = sorted(
        [(k, v) for k, v in signals.items() if isinstance(v, dict)],
        key=lambda x: x[1].get('ratio', 0),
        reverse=True,
    )

    rows = []
    for sig_key, sig_data in sorted_signals:
        label    = sig_data.get('label', sig_key)
        ratio    = sig_data.get('ratio', 0)
        pc       = sig_data.get('post_count', sig_data.get('repeat_authors_7d', '-'))
        bar_len  = min(int(ratio), 100)
        bar_color = '#FF4B4B' if ratio >= 10 else ('#FFA500' if ratio >= 5 else '#ADB5BD')
        bar_html  = (
            f'<div style="background:#F0F2F6;border-radius:4px;height:8px;width:100%;">'
            f'<div style="background:{bar_color};border-radius:4px;height:8px;width:{bar_len}%;"></div>'
            f'</div>'
        )
        rows.append((label, ratio, pc, bar_html))

    # 2열 그리드
    sig_cols = st.columns(2)
    for i, (label, ratio, pc, bar_html) in enumerate(rows):
        with sig_cols[i % 2]:
            st.markdown(
                f"""
                <div style="padding:10px 14px; margin-bottom:8px;
                            background:white; border:1px solid #E9ECEF;
                            border-radius:8px;">
                    <div style="font-size:0.85rem; font-weight:600; margin-bottom:4px;">
                        {label}
                    </div>
                    {bar_html}
                    <div style="font-size:0.78rem; color:#6C757D; margin-top:4px;">
                        관련 게시글: {pc}건 &nbsp;|&nbsp; 비율: <b>{ratio}%</b>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.caption("게임 특화 지표 데이터가 없습니다.")

st.markdown("---")

# ── 분석 회차 정보 ───────────────────────────────────────────────────
with st.expander(f"🔍 이 분석 회차 정보 (run_id: {run_id})"):
    st.markdown(f"""
    **분석 회차 ID**: `{run_id}`

    이 ID로 분석에 사용된 게시글 원본을 조회할 수 있습니다.

    - **Google Sheets** → `분석대상게시글` 탭 → `run_id` 컬럼 필터: `{run_id}`
    - **재분석 명령어**: `python run_analysis.py --rerun {run_id}`

    분석 결과가 마음에 들지 않거나 재확인이 필요할 때 동일한 게시글로 다시 분석할 수 있습니다.
    """)
