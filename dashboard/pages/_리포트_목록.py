"""
DC-Pickaxe Analytics — 리포트 목록 v10
일간/주간 리포트를 두 열로 나란히 나열 · 최신 순 · [보기] 클릭 → 상세
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='리포트 목록 — DC-Pickaxe',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, render_sidebar_nav
inject_css()
render_sidebar_nav()

with st.sidebar:
    st.caption('전체 분석 이력 목록')
    st.divider()
    st.caption('DC-Pickaxe Analytics v10')


@st.cache_data(ttl=180)
def load_daily_index():
    from sheets.reader import get_daily_report_index
    return get_daily_report_index()


@st.cache_data(ttl=180)
def load_weekly_index():
    from sheets.reader import get_weekly_report_index
    return get_weekly_report_index()


# ── 브레드크럼 ───────────────────────────────────────────────────────
bc1, bc2, bc3 = st.columns([0.7, 0.15, 5])
with bc1:
    st.page_link('app.py', label='🏠 홈')
with bc2:
    st.caption('›')
with bc3:
    st.caption('**리포트 목록**')

st.title('리포트 목록')
st.caption('최신 리포트가 상단에 표시됩니다')
st.divider()

try:
    daily_index = load_daily_index()
except Exception as e:
    st.error(f'일간 데이터 오류: {e}')
    daily_index = []

try:
    weekly_index = load_weekly_index()
except Exception as e:
    st.error(f'주간 데이터 오류: {e}')
    weekly_index = []

col_daily, col_sep, col_weekly = st.columns([5, 0.1, 4])

with col_daily:
    st.markdown(
        '<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.06em;'
        'color:#64748B;text-transform:uppercase;margin-bottom:6px;">'
        '📋 일간 이슈 리포트</div>',
        unsafe_allow_html=True,
    )
    st.caption('이슈 감지 시에만 발행')
    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    if not daily_index:
        st.info('일간 리포트 데이터가 없습니다.')
    else:
        for item in daily_index:
            d  = item['date']
            ic = item['issue_count']
            tc = item['total_count']
            with st.container(border=True):
                r1, r2 = st.columns([4, 1])
                with r1:
                    if ic > 0:
                        badge = (
                            f'<span style="display:inline-block;background:#FEE2E2;'
                            f'border:1px solid #EF4444;border-radius:20px;'
                            f'padding:1px 8px;font-size:0.72rem;font-weight:700;'
                            f'color:#EF4444;margin-left:6px;">⚠ 이슈 {ic}개</span>'
                        )
                    else:
                        badge = (
                            '<span style="display:inline-block;background:#DCFCE7;'
                            'border:1px solid #10B981;border-radius:20px;'
                            'padding:1px 8px;font-size:0.72rem;font-weight:700;'
                            'color:#10B981;margin-left:6px;">✓ 정상</span>'
                        )
                    st.markdown(
                        f'<div style="font-size:0.9rem;font-weight:600;">'
                        f'{d}{badge}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption(f'갤러리 {tc}개 분석')
                with r2:
                    if st.button('보기', key=f'ld_{d}', use_container_width=True):
                        st.session_state['report_date'] = d
                        st.switch_page('pages/_일간_리포트.py')

with col_sep:
    st.markdown(
        '<div style="width:1px;background:#E2E8F0;min-height:400px;margin-top:52px;"></div>',
        unsafe_allow_html=True,
    )

with col_weekly:
    st.markdown(
        '<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.06em;'
        'color:#64748B;text-transform:uppercase;margin-bottom:6px;">'
        '📊 주간 분석 리포트</div>',
        unsafe_allow_html=True,
    )
    st.caption('매주 월요일 정기 발행')
    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

    if not weekly_index:
        st.info('주간 리포트 데이터가 없습니다.')
    else:
        for item in weekly_index:
            ws = item['week_start']
            we = item['week_end']
            with st.container(border=True):
                w1, w2 = st.columns([4, 1])
                with w1:
                    st.markdown(
                        f'<div style="font-size:0.9rem;font-weight:600;">'
                        f'{ws} ~ {we}</div>',
                        unsafe_allow_html=True,
                    )
                    st.caption('주간 분석 리포트')
                with w2:
                    if st.button('보기', key=f'lw_{ws}', use_container_width=True):
                        st.session_state['report_week_start'] = ws
                        st.switch_page('pages/_주간_리포트.py')
