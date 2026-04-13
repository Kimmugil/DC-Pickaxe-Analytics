"""
DC-Pickaxe Analytics — 메인 대시보드
정보 흐름: 타이틀 → 분석 현황 → 최신 주간 요약 → 캘린더
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

from dashboard.dash_styles import inject_css, sec_header, stat_card
inject_css()

# ── 캘린더 클릭 네비게이션 ──────────────────────────────────────────
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


def _calendar_html(year: int, month: int, cal_data: dict, today: date) -> str:
    cal        = calendar.monthcalendar(year, month)
    month_name = f"{year}년 {month}월"
    dow_headers = ''.join(
        f'<div style="text-align:center;font-size:0.7rem;font-weight:700;color:#94A3B8;padding:4px 0;">{d}</div>'
        for d in ['월', '화', '수', '목', '금', '토', '일']
    )
    cells = []
    for week in cal:
        for day in week:
            if day == 0:
                cells.append('<div></div>')
                continue
            d           = date(year, month, day)
            d_str       = d.strftime('%Y-%m-%d')
            is_today    = d == today
            report_type = cal_data.get(d_str)
            today_style = 'outline:2px solid #E8A020;outline-offset:-2px;' if is_today else ''
            if report_type:
                if report_type == 'both':
                    badge    = '<span style="font-size:0.58rem;font-weight:700;padding:1px 4px;border-radius:4px;margin-top:2px;background:#E8A020;color:white;">주+일</span>'
                    nav_type = 'weekly'
                elif report_type == 'weekly':
                    badge    = '<span style="font-size:0.58rem;font-weight:700;padding:1px 4px;border-radius:4px;margin-top:2px;background:#E8A020;color:white;">주</span>'
                    nav_type = 'weekly'
                else:
                    badge    = '<span style="font-size:0.58rem;font-weight:700;padding:1px 4px;border-radius:4px;margin-top:2px;background:#475569;color:white;">일</span>'
                    nav_type = 'daily'
                cells.append(
                    f'<div style="aspect-ratio:1;display:flex;flex-direction:column;align-items:center;'
                    f'justify-content:center;border-radius:8px;background:#FEF3C7;min-height:34px;{today_style}">'
                    f'<a href="?nav_date={d_str}&nav_type={nav_type}" '
                    f'style="text-decoration:none;color:#0F172A;font-weight:700;font-size:0.82rem;'
                    f'display:flex;flex-direction:column;align-items:center;justify-content:center;width:100%;height:100%;">'
                    f'{day}{badge}</a></div>'
                )
            else:
                cells.append(
                    f'<div style="aspect-ratio:1;display:flex;align-items:center;justify-content:center;'
                    f'border-radius:8px;font-size:0.82rem;color:#475569;min-height:34px;{today_style}">{day}</div>'
                )
    grid = ''.join(cells)
    return (
        f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;'
        f'padding:16px 18px;margin-bottom:14px;box-shadow:0 1px 3px rgba(15,23,42,.05);">'
        f'<div style="font-size:0.9rem;font-weight:700;color:#0F172A;margin-bottom:10px;">{month_name}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;">'
        f'{dow_headers}{grid}'
        f'</div></div>'
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
        with st.spinner(f'분석 중... ({today_str})'):
            success, output = run_analysis_now(today_str)
        if success:
            st.cache_data.clear()
            st.success('완료!')
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
        '<div style="font-size:0.68rem;color:#334155;">DC-Pickaxe Analytics v6</div>',
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

# ── 페이지 타이틀 ─────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:1.75rem;font-weight:800;color:#0F172A;line-height:1.15;margin-bottom:3px;">'
    '⛏️ DC-Pickaxe Analytics</div>'
    '<div style="font-size:0.85rem;color:#64748B;margin-bottom:18px;">'
    '키우기 장르 갤러리 자동 분석 대시보드</div>',
    unsafe_allow_html=True,
)

# ── 분석 현황 스트립 ──────────────────────────────────────────────────
last_date   = overall.get('date', '-')
total_posts = overall.get('total_posts', 0)
st.markdown(
    f'<div style="background:#F1F5F9;border:1px solid #E2E8F0;border-radius:10px;'
    f'padding:9px 16px;font-size:0.78rem;color:#475569;'
    f'display:flex;gap:20px;margin-bottom:20px;">'
    f'<span>마지막 분석: <b style="color:#1E293B">{last_date}</b></span>'
    f'<span>누적 수집: <b style="color:#1E293B">{total_posts:,}건</b></span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI 카드 (3열 Bento) ──────────────────────────────────────────────
k1, k2, k3 = st.columns(3)
with k1:
    v = overall.get('new_posts_today', 0)
    st.markdown(
        stat_card('24h 신규 게시글', f'{v:,}건',
                  sub=f'기준일: {overall.get("date", "-")}',
                  tooltip=f'{last_date} 00:00~23:59 전체 갤러리 합산'),
        unsafe_allow_html=True,
    )
with k2:
    v = overall.get('new_posts_7d', 0)
    st.markdown(
        stat_card('최근 7일 신규', f'{v:,}건', sub='전체 갤러리 합산',
                  tooltip='마지막 분석일 기준 7일 이내 전체 갤러리 게시글 수'),
        unsafe_allow_html=True,
    )
with k3:
    v = overall.get('total_posts', 0)
    st.markdown(
        stat_card('누적 수집 게시글', f'{v:,}건', sub='전체 갤러리 누적',
                  tooltip='수집된 전체 게시글 합산 (stats 시트 기준)'),
        unsafe_allow_html=True,
    )

st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)

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
            st.markdown(
                '<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;'
                'padding:22px 26px;margin-bottom:10px;border-left:5px solid #E8A020;'
                'box-shadow:0 1px 3px rgba(15,23,42,.06);">',
                unsafe_allow_html=True,
            )
            st.markdown(txt)
            st.markdown('</div>', unsafe_allow_html=True)
            if ws_date:
                st.markdown(
                    f'<a href="?nav_date={ws_date}&nav_type=weekly" '
                    f'style="font-size:0.82rem;color:#E8A020;text-decoration:none;font-weight:600;">'
                    f'→ 전체 주간 리포트 보기</a>',
                    unsafe_allow_html=True,
                )
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
except Exception:
    pass

# ── 리포트 캘린더 ─────────────────────────────────────────────────────
st.markdown(sec_header('리포트 캘린더'), unsafe_allow_html=True)
st.markdown(
    '<div style="font-size:0.78rem;color:#64748B;margin-bottom:12px;">'
    '날짜 클릭 시 해당 리포트로 이동합니다. 주간 리포트: 매주 <b>월요일</b></div>',
    unsafe_allow_html=True,
)
prev_month_date = today.replace(day=1) - timedelta(days=1)
prev_y, prev_m  = prev_month_date.year, prev_month_date.month
curr_y, curr_m  = today.year, today.month
col_prev, col_curr = st.columns(2)
with col_prev:
    st.markdown(_calendar_html(prev_y, prev_m, cal_data, today), unsafe_allow_html=True)
with col_curr:
    st.markdown(_calendar_html(curr_y, curr_m, cal_data, today), unsafe_allow_html=True)
