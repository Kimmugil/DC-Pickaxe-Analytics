"""
DC-Pickaxe Analytics — 리포트 목록 v9
IA 목적: 콘텐츠 탐색 허브 — 날짜 몰라도 리포트 찾을 수 있는 페이지
기능:
  - 일간/주간 탭 구분
  - 월 필터 드롭다운
  - 이슈 수 + 게시글 수 표시
  - [보기] 클릭 → 해당 리포트로 즉시 이동
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

from dashboard.dash_styles import inject_css
inject_css()


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('**⛏️ DC-Pickaxe**')
    st.divider()
    st.page_link('app.py', label='🏠 홈으로', use_container_width=True)
    st.divider()
    st.caption('리포트 목록 페이지')
    st.caption('원하는 날짜의 리포트를 찾아 이동하세요.')


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=180)
def load_daily_index():
    from sheets.reader import get_daily_report_index
    return get_daily_report_index()


@st.cache_data(ttl=180)
def load_weekly_index():
    from sheets.reader import get_weekly_report_index
    return get_weekly_report_index()


# ── 브레드크럼 ───────────────────────────────────────────────────────
bc1, bc2, bc3 = st.columns([0.8, 0.15, 4])
with bc1:
    st.page_link('app.py', label='🏠 홈')
with bc2:
    st.caption('›')
with bc3:
    st.caption('**리포트 목록**')

# ── 페이지 타이틀 ─────────────────────────────────────────────────────
st.title('리포트 목록')
st.caption('전체 분석 이력 조회 · 월별 필터 후 리포트를 열어보세요')

# ── 탭 ───────────────────────────────────────────────────────────────
tab_daily, tab_weekly = st.tabs(['📋 일간 이슈 리포트', '📊 주간 분석 리포트'])

# ── 일간 탭 ──────────────────────────────────────────────────────────
with tab_daily:
    try:
        daily_index = load_daily_index()
    except Exception as e:
        st.error(f'데이터 로딩 오류: {e}')
        daily_index = []

    if not daily_index:
        st.info('일간 리포트 데이터가 없습니다.')
    else:
        # 월 필터
        months = sorted(
            set(item['date'][:7] for item in daily_index),
            reverse=True,
        )
        month_labels = {m: f'{m[:4]}년 {m[5:7]}월 ({sum(1 for i in daily_index if i["date"].startswith(m))}건)' for m in months}
        sel_month = st.selectbox(
            '월 선택',
            options=months,
            format_func=lambda m: month_labels[m],
            key='dl_month_filter',
        )

        month_items = [item for item in daily_index if item['date'].startswith(sel_month)]
        st.caption(f'{sel_month[:4]}년 {sel_month[5:7]}월 · {len(month_items)}건')
        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

        # 컬럼 헤더
        h1, h2, h3, h4, h5 = st.columns([3, 2, 2, 2, 1])
        with h1:
            st.markdown(
                '<span style="font-size:0.75rem;font-weight:700;letter-spacing:0.05em;'
                'color:#94A3B8;text-transform:uppercase;">날짜</span>',
                unsafe_allow_html=True,
            )
        with h2:
            st.markdown(
                '<span style="font-size:0.75rem;font-weight:700;letter-spacing:0.05em;'
                'color:#94A3B8;text-transform:uppercase;">이슈</span>',
                unsafe_allow_html=True,
            )
        with h3:
            st.markdown(
                '<span style="font-size:0.75rem;font-weight:700;letter-spacing:0.05em;'
                'color:#94A3B8;text-transform:uppercase;">갤러리 수</span>',
                unsafe_allow_html=True,
            )
        with h4:
            st.markdown(
                '<span style="font-size:0.75rem;font-weight:700;letter-spacing:0.05em;'
                'color:#94A3B8;text-transform:uppercase;">24H 신규</span>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div style="height:1px;background:#E2E8F0;margin-bottom:6px;"></div>',
            unsafe_allow_html=True,
        )

        for item in month_items:
            d   = item['date']
            ic  = item['issue_count']
            tc  = item['total_count']
            np  = item['new_posts_today']

            r1, r2, r3, r4, r5 = st.columns([3, 2, 2, 2, 1])
            with r1:
                st.markdown(f'**{d}**')
            with r2:
                if ic > 0:
                    st.markdown(
                        f'<span style="color:#EF4444;font-weight:700;font-size:0.85rem;">⚠ {ic}개</span>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<span style="color:#10B981;font-size:0.85rem;">✓ 없음</span>',
                        unsafe_allow_html=True,
                    )
            with r3:
                st.caption(f'{tc}개')
            with r4:
                st.caption(f'{np:,}건' if np else '-')
            with r5:
                if st.button('보기', key=f'list_d_{d}', use_container_width=True):
                    st.session_state['report_date'] = d
                    st.switch_page('pages/2_일간_리포트.py')

# ── 주간 탭 ──────────────────────────────────────────────────────────
with tab_weekly:
    try:
        weekly_index = load_weekly_index()
    except Exception as e:
        st.error(f'데이터 로딩 오류: {e}')
        weekly_index = []

    if not weekly_index:
        st.info('주간 리포트 데이터가 없습니다.')
    else:
        st.caption(f'전체 {len(weekly_index)}개 주간 리포트')
        st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

        # 컬럼 헤더
        wh1, wh2, wh3 = st.columns([4, 3, 1])
        with wh1:
            st.markdown(
                '<span style="font-size:0.75rem;font-weight:700;letter-spacing:0.05em;'
                'color:#94A3B8;text-transform:uppercase;">분석 기간</span>',
                unsafe_allow_html=True,
            )
        with wh2:
            st.markdown(
                '<span style="font-size:0.75rem;font-weight:700;letter-spacing:0.05em;'
                'color:#94A3B8;text-transform:uppercase;">주 시작일</span>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div style="height:1px;background:#E2E8F0;margin-bottom:6px;"></div>',
            unsafe_allow_html=True,
        )

        for item in weekly_index:
            ws = item['week_start']
            we = item['week_end']

            wr1, wr2, wr3 = st.columns([4, 3, 1])
            with wr1:
                st.markdown(f'**{ws}** ~ {we}')
            with wr2:
                st.caption(f'월요일 기준 · 7일')
            with wr3:
                if st.button('보기', key=f'list_w_{ws}', use_container_width=True):
                    st.session_state['report_week_start'] = ws
                    st.switch_page('pages/3_주간_리포트.py')
