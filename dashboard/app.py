"""
DC-Pickaxe Analytics — 메인 대시보드 (캘린더 뷰)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import calendar
import streamlit as st
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='DC-Pickaxe Analytics',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, stat_card, sec_header, cross_card
inject_css()

# ── 캘린더 클릭 네비게이션 처리 ─────────────────────────────────────
params = st.query_params
if 'nav_date' in params:
    nav_date = params['nav_date']
    nav_type = params.get('nav_type', 'daily')
    st.session_state['report_date'] = nav_date
    if nav_type == 'weekly':
        st.session_state['report_week_start'] = nav_date
        st.switch_page('pages/3_주간_리포트.py')
    else:
        st.switch_page('pages/2_일간_리포트.py')


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_calendar_data():
    from sheets.reader import get_calendar_data
    return get_calendar_data()


@st.cache_data(ttl=300)
def load_latest_weekly():
    from sheets.reader import get_latest_weekly_summary
    return get_latest_weekly_summary()


@st.cache_data(ttl=300)
def load_available_dates():
    from sheets.reader import get_available_dates
    return get_available_dates()


# ── 캘린더 HTML 생성 ─────────────────────────────────────────────────
def _calendar_html(year: int, month: int, cal_data: dict, today: date) -> str:
    cal = calendar.monthcalendar(year, month)
    month_name = f"{year}년 {month}월"
    dow_headers = ''.join(
        f'<div class="cal-dow">{d}</div>'
        for d in ['월', '화', '수', '목', '금', '토', '일']
    )
    cells = []
    for week in cal:
        for day in week:
            if day == 0:
                cells.append('<div class="cal-cell empty"></div>')
                continue
            d = date(year, month, day)
            d_str      = d.strftime('%Y-%m-%d')
            today_cls  = ' cal-today' if d == today else ''
            report_type = cal_data.get(d_str)

            if report_type:
                if report_type == 'both':
                    badge    = '<span class="cal-badge cal-badge-b">주+일</span>'
                    nav_type = 'weekly'
                elif report_type == 'weekly':
                    badge    = '<span class="cal-badge cal-badge-w">주</span>'
                    nav_type = 'weekly'
                else:
                    badge    = '<span class="cal-badge cal-badge-d">일</span>'
                    nav_type = 'daily'
                cells.append(
                    f'<div class="cal-cell has-report{today_cls}">'
                    f'<a href="?nav_date={d_str}&nav_type={nav_type}">'
                    f'{day}{badge}</a></div>'
                )
            else:
                cells.append(f'<div class="cal-cell{today_cls}">{day}</div>')

    grid = ''.join(cells)
    return (
        f'<div class="cal-wrap">'
        f'<div class="cal-title">{month_name}</div>'
        f'<div class="cal-grid">{dow_headers}{grid}</div>'
        f'</div>'
    )


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.1rem;font-weight:800;color:#0A0A0A;margin-bottom:2px;">'
        '⛏️ DC-Pickaxe</div>'
        '<div style="font-size:0.73rem;color:#888888;margin-bottom:16px;">'
        '키우기 갤러리 분석 대시보드</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    today_str = datetime.now().strftime('%Y-%m-%d')
    st.markdown(
        f'<div style="font-size:0.75rem;color:#555555;margin-bottom:10px;">'
        f'오늘: <b style="color:#0A0A0A">{today_str}</b></div>',
        unsafe_allow_html=True,
    )

    run_btn = st.button('분석 실행 (오늘)', use_container_width=True, key='btn_run_daily')
    if run_btn:
        from dashboard.analysis_runner import run_analysis_now
        with st.spinner(f'분석 중... ({today_str} 기준)'):
            success, output = run_analysis_now(today_str)
        if success:
            st.cache_data.clear()
            st.success('분석 완료!')
            st.rerun()
        else:
            st.error('분석 실패')
            with st.expander('오류 로그'):
                st.code(output[:3000])

    st.divider()
    st.markdown(
        '<div style="font-size:0.7rem;color:#888888;">캘린더에서 날짜를 클릭하면<br>해당 리포트로 이동합니다.</div>'
        '<div style="font-size:0.7rem;color:#888888;margin-top:6px;">'
        '<span style="background:#555555;color:white;border-radius:3px;padding:1px 5px;font-size:0.65rem;">일</span> 일간 이슈 리포트<br>'
        '<span style="background:#0A0A0A;color:white;border-radius:3px;padding:1px 5px;font-size:0.65rem;">주</span> 주간 분석 리포트</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown(
        '<div style="font-size:0.7rem;color:#AAAAAA;">DC-Pickaxe Analytics</div>',
        unsafe_allow_html=True,
    )


# ── 메인 콘텐츠 ──────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:1.5rem;font-weight:800;color:#0A0A0A;margin-bottom:4px;">'
    '⛏️ DC-Pickaxe Analytics</div>'
    '<div style="font-size:0.85rem;color:#555555;margin-bottom:20px;">'
    '키우기 장르 갤러리 자동 분석 대시보드</div>',
    unsafe_allow_html=True,
)

# ── 캘린더 데이터 ────────────────────────────────────────────────────
try:
    cal_data = load_calendar_data()
except Exception as e:
    st.warning(f'캘린더 데이터 로딩 실패: {e}')
    cal_data = {}

# ── KPI 박스 ─────────────────────────────────────────────────────────
today = date.today()
daily_count  = sum(1 for v in cal_data.values() if v in ('daily', 'both'))
weekly_count = sum(1 for v in cal_data.values() if v in ('weekly', 'both'))

try:
    avail_dates = load_available_dates()
    last_daily = avail_dates[0] if avail_dates else '-'
except Exception:
    last_daily = '-'

try:
    latest_weekly = load_latest_weekly()
    last_weekly = latest_weekly.get('week_start', '-') if latest_weekly else '-'
except Exception:
    last_weekly = '-'

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        stat_card('일간 이슈 리포트', f'{daily_count}건',
                  sub=f'최근: {last_daily}',
                  tooltip='이슈가 탐지된 날짜 수 (이슈 점수 3점 이상)'),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        stat_card('주간 분석 리포트', f'{weekly_count}건',
                  sub=f'최근: {last_weekly}',
                  tooltip='주간 분석이 발행된 주 수 (매주 월요일 자동 발행)'),
        unsafe_allow_html=True,
    )
with k3:
    total_reports = len(cal_data)
    st.markdown(
        stat_card('전체 발행 리포트', f'{total_reports}건',
                  sub='일간+주간 합산',
                  tooltip='캘린더에 표시된 전체 리포트 수'),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── 캘린더 ───────────────────────────────────────────────────────────
st.markdown(sec_header('리포트 캘린더'), unsafe_allow_html=True)
st.markdown(
    '<div style="font-size:0.78rem;color:#888888;margin-bottom:12px;">'
    '날짜를 클릭하면 해당 리포트로 이동합니다.</div>',
    unsafe_allow_html=True,
)

# 이번 달 + 지난 달 캘린더 2개
prev_month_date = (today.replace(day=1) - timedelta(days=1))
prev_y, prev_m  = prev_month_date.year, prev_month_date.month
curr_y, curr_m  = today.year, today.month

col_prev, col_curr = st.columns(2)
with col_prev:
    st.markdown(
        _calendar_html(prev_y, prev_m, cal_data, today),
        unsafe_allow_html=True,
    )
with col_curr:
    st.markdown(
        _calendar_html(curr_y, curr_m, cal_data, today),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── 최신 주간 요약 위젯 ──────────────────────────────────────────────
st.markdown(sec_header('최신 주간 요약'), unsafe_allow_html=True)

try:
    latest_weekly = load_latest_weekly()
    if latest_weekly:
        ws  = latest_weekly.get('week_start', '')
        we  = latest_weekly.get('week_end', '')
        txt = str(latest_weekly.get('ai_weekly_summary', ''))
        st.markdown(
            f'<div style="font-size:0.78rem;color:#888888;margin-bottom:8px;">'
            f'{ws} ~ {we}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            cross_card(txt.replace('\n', '<br>') if txt else '요약 없음'),
            unsafe_allow_html=True,
        )
        if ws:
            st.markdown(
                f'<a href="?nav_date={ws}&nav_type=weekly" '
                f'style="font-size:0.8rem;color:#333333;">→ 전체 주간 리포트 보기</a>',
                unsafe_allow_html=True,
            )
    else:
        st.info('아직 주간 분석 데이터가 없습니다.')
except Exception as e:
    st.info(f'주간 요약 로딩 실패: {e}')
