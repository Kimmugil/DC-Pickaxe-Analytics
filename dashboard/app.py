"""
DC-Pickaxe Analytics — 메인 대시보드 (캘린더 뷰)
정보 흐름: 개요 KPI → 최신 주간 요약 → 리포트 캘린더 → 분석 실행
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

from dashboard.dash_styles import inject_css, stat_card, sec_header
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
def load_overall_stats():
    from sheets.reader import get_latest_overall_stats
    return get_latest_overall_stats()


# ── 캘린더 HTML 생성 ─────────────────────────────────────────────────
def _calendar_html(year: int, month: int, cal_data: dict, today: date) -> str:
    cal        = calendar.monthcalendar(year, month)
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
            d           = date(year, month, day)
            d_str       = d.strftime('%Y-%m-%d')
            today_cls   = ' cal-today' if d == today else ''
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
        '<div style="font-size:1.1rem;font-weight:800;color:#F1F5F9;margin-bottom:2px;">⛏️ DC-Pickaxe</div>'
        '<div style="font-size:0.73rem;color:#64748B;margin-bottom:16px;">키우기 갤러리 분석 대시보드</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    today_str = datetime.now().strftime('%Y-%m-%d')
    st.markdown(
        f'<div style="font-size:0.75rem;color:#64748B;margin-bottom:10px;">'
        f'오늘: <b style="color:#CBD5E1">{today_str}</b></div>',
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
        '<div style="font-size:0.72rem;color:#475569;line-height:1.9;">'
        '날짜 클릭 → 리포트 이동<br>'
        '<span style="background:#475569;color:white;border-radius:3px;padding:1px 5px;font-size:0.65rem;">일</span>'
        '&nbsp;이슈 리포트&nbsp;&nbsp;'
        '<span style="background:#E8A020;color:white;border-radius:3px;padding:1px 5px;font-size:0.65rem;">주</span>'
        '&nbsp;주간 리포트'
        '</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown(
        '<div style="font-size:0.68rem;color:#334155;">DC-Pickaxe Analytics v5</div>',
        unsafe_allow_html=True,
    )


# ── 데이터 로드 ──────────────────────────────────────────────────────
today = date.today()

try:
    cal_data = load_calendar_data()
except Exception:
    cal_data = {}

try:
    overall = load_overall_stats()
except Exception:
    overall = {}

# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:1.6rem;font-weight:800;color:#0F172A;line-height:1.2;margin-bottom:2px;">⛏️ DC-Pickaxe Analytics</div>'
    '<div style="font-size:0.85rem;color:#475569;margin-bottom:14px;">키우기 장르 갤러리 자동 분석 대시보드</div>',
    unsafe_allow_html=True,
)

# ── 상태 표시줄 ───────────────────────────────────────────────────────
last_date   = overall.get('date', '-')
total_posts = overall.get('total_posts', 0)
st.markdown(
    f'<div class="status-bar">'
    f'<span>마지막 분석: <b>{last_date}</b></span>'
    f'<span>누적 수집: <b>{total_posts:,}건</b></span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI 카드 (Bento 3열) ─────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
with k1:
    val = overall.get('new_posts_today', 0)
    sub = f'기준일: {overall.get("date", "-")}'
    st.markdown(
        stat_card(
            '24h 신규 게시글', f'{val:,}건', sub=sub,
            tooltip='가장 최근 분석일 당일(00:00~23:59) 전체 갤러리 합산 신규 게시글 수',
        ),
        unsafe_allow_html=True,
    )
with k2:
    val = overall.get('new_posts_7d', 0)
    st.markdown(
        stat_card(
            '최근 7일 신규', f'{val:,}건', sub='전체 갤러리 합산',
            tooltip='가장 최근 분석일 기준 7일 이내 전체 갤러리 합산 게시글 수',
        ),
        unsafe_allow_html=True,
    )
with k3:
    total = overall.get('total_posts', 0)
    st.markdown(
        stat_card(
            '누적 게시글', f'{total:,}건', sub='전체 갤러리 누적',
            tooltip='수집된 전체 게시글 합산 (stats 시트 기준)',
        ),
        unsafe_allow_html=True,
    )

st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)

# ── 최신 주간 요약 ────────────────────────────────────────────────────
try:
    latest_weekly = load_latest_weekly()
    if latest_weekly:
        ws_date = latest_weekly.get('week_start', '')
        we_date = latest_weekly.get('week_end', '')
        txt     = str(latest_weekly.get('ai_weekly_summary', ''))
        if txt and not txt.startswith('>'):
            st.markdown(sec_header('최신 주간 요약'), unsafe_allow_html=True)
            st.markdown(
                f'<div style="font-size:0.78rem;color:#64748B;margin-bottom:8px;">'
                f'분석 기간: <b style="color:#1E293B">{ws_date} ~ {we_date}</b></div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div class="summary-card">', unsafe_allow_html=True)
            st.markdown(txt)
            st.markdown('</div>', unsafe_allow_html=True)
            if ws_date:
                st.markdown(
                    f'<a href="?nav_date={ws_date}&nav_type=weekly" '
                    f'style="font-size:0.8rem;color:#E8A020;text-decoration:none;font-weight:600;">'
                    f'→ 전체 주간 리포트 보기</a>',
                    unsafe_allow_html=True,
                )
            st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
except Exception:
    pass

# ── 리포트 캘린더 ─────────────────────────────────────────────────────
st.markdown(sec_header('리포트 캘린더'), unsafe_allow_html=True)
st.markdown(
    '<div style="font-size:0.78rem;color:#64748B;margin-bottom:12px;">'
    '날짜를 클릭하면 해당 리포트로 이동합니다. '
    '주간 리포트 생성일: 매주 <b>월요일</b></div>',
    unsafe_allow_html=True,
)

prev_month_date = (today.replace(day=1) - timedelta(days=1))
prev_y, prev_m  = prev_month_date.year, prev_month_date.month
curr_y, curr_m  = today.year, today.month

col_prev, col_curr = st.columns(2)
with col_prev:
    st.markdown(_calendar_html(prev_y, prev_m, cal_data, today), unsafe_allow_html=True)
with col_curr:
    st.markdown(_calendar_html(curr_y, curr_m, cal_data, today), unsafe_allow_html=True)
