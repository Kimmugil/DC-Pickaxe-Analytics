"""
DC-Pickaxe Analytics — 메인 대시보드 v9
IA 개편: 홈을 Hub로 재설계
  - 빠른 리포트 접근: 최근 일간/주간 리포트 퀵링크 (캘린더 클릭 없이)
  - KPI delta: 오늘 vs 7일 평균 맥락 제공
  - 최신 주간 요약: 접이식(expander)로 아래로 내림
  - 캘린더: 가장 하단 (날짜 탐색 보조 수단)
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

from dashboard.dash_styles import inject_css
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
def load_overall_stats():
    from sheets.reader import get_latest_overall_stats
    return get_latest_overall_stats()


@st.cache_data(ttl=300)
def load_daily_index():
    from sheets.reader import get_daily_report_index
    return get_daily_report_index()


@st.cache_data(ttl=300)
def load_weekly_index():
    from sheets.reader import get_weekly_report_index
    return get_weekly_report_index()


@st.cache_data(ttl=300)
def load_latest_weekly():
    from sheets.reader import get_latest_weekly_summary
    return get_latest_weekly_summary()


@st.cache_data(ttl=300)
def load_calendar_data():
    from sheets.reader import get_calendar_data
    return get_calendar_data()


def _calendar_html(year: int, month: int, cal_data: dict, today: date) -> str:
    cal_obj    = calendar.monthcalendar(year, month)
    month_name = f"{year}년 {month}월"
    dow_headers = ''.join(
        f'<div style="text-align:center;font-size:0.7rem;font-weight:700;color:#94A3B8;padding:4px 0;">{d}</div>'
        for d in ['월', '화', '수', '목', '금', '토', '일']
    )
    cells = []
    for week in cal_obj:
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
                    badge_tx, nav_type, badge_bg = '주+일', 'weekly', '#E8A020'
                elif report_type == 'weekly':
                    badge_tx, nav_type, badge_bg = '주', 'weekly', '#E8A020'
                else:
                    badge_tx, nav_type, badge_bg = '일', 'daily', '#475569'
                badge = (
                    f'<span style="font-size:0.55rem;font-weight:700;padding:1px 4px;'
                    f'border-radius:3px;margin-top:2px;background:{badge_bg};color:white;">'
                    f'{badge_tx}</span>'
                )
                cells.append(
                    f'<div style="aspect-ratio:1;display:flex;flex-direction:column;align-items:center;'
                    f'justify-content:center;border-radius:8px;background:#FEF3C7;min-height:34px;{today_style}">'
                    f'<a href="?nav_date={d_str}&nav_type={nav_type}" '
                    f'style="text-decoration:none;color:#0F172A;font-weight:700;font-size:0.82rem;'
                    f'display:flex;flex-direction:column;align-items:center;justify-content:center;'
                    f'width:100%;height:100%;">{day}{badge}</a></div>'
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
        f'{dow_headers}{grid}</div></div>'
    )


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('**⛏️ DC-Pickaxe**')
    st.caption('키우기 갤러리 분석 대시보드')
    st.divider()
    today_str = datetime.now().strftime('%Y-%m-%d')
    st.caption(f'오늘: **{today_str}**')
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
    st.caption('DC-Pickaxe Analytics v9')


# ── 데이터 로드 ──────────────────────────────────────────────────────
today = date.today()
try:
    overall = load_overall_stats()
except Exception:
    overall = {}

# ── 페이지 타이틀 ─────────────────────────────────────────────────────
st.title('⛏️ DC-Pickaxe Analytics')
st.caption('키우기 장르 갤러리 자동 분석 대시보드')

# ── 분석 현황 상태 표시 ───────────────────────────────────────────────
last_date   = overall.get('date', '-')
total_posts = overall.get('total_posts', 0)
st.markdown(
    f'<div style="display:inline-flex;align-items:center;gap:8px;background:#F8FAFC;'
    f'border:1px solid #E2E8F0;border-radius:10px;padding:8px 14px;'
    f'font-size:0.82rem;color:#475569;margin-bottom:4px;">'
    f'<span style="color:#10B981;font-size:0.9rem;">●</span>'
    f'마지막 분석&nbsp;<b style="color:#0F172A">{last_date}</b>'
    f'&nbsp;&nbsp;·&nbsp;&nbsp;누적 수집&nbsp;<b style="color:#0F172A">{total_posts:,}건</b>'
    f'</div>',
    unsafe_allow_html=True,
)
st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

# ── KPI — 24h vs 7일 평균 delta ───────────────────────────────────────
new_today = overall.get('new_posts_today', 0)
new_7d    = overall.get('new_posts_7d', 0)
daily_avg = round(new_7d / 7, 1) if new_7d else 0
delta_val = round(new_today - daily_avg, 1)

k1, k2, k3 = st.columns(3)
with k1:
    st.metric(
        '24H 신규 게시글',
        f'{new_today:,}건',
        delta=f'{delta_val:+.0f} vs 7일 평균',
        delta_color='normal',
        help=f'{last_date} 00:00~23:59 합산 / 7일 일평균 {daily_avg:.1f}건 대비',
    )
with k2:
    st.metric('최근 7일 신규', f'{new_7d:,}건',
              help='마지막 분석일 기준 7일 이내 전체 갤러리')
with k3:
    st.metric('누적 수집', f'{total_posts:,}건',
              help='전체 게시글 누적 합산')

st.divider()

# ── 빠른 리포트 접근 — Hub 핵심 섹션 ─────────────────────────────────
col_hdr, col_more = st.columns([5, 1])
with col_hdr:
    st.subheader('📌 빠른 리포트 접근')
with col_more:
    st.markdown('<div style="padding-top:10px;"></div>', unsafe_allow_html=True)
    st.page_link('pages/1_리포트_목록.py', label='전체 목록 →')

col_daily, col_sep, col_weekly = st.columns([5, 0.2, 4])

with col_daily:
    st.markdown(
        '<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.06em;'
        'color:#64748B;text-transform:uppercase;margin-bottom:8px;">📋 최근 일간 리포트</div>',
        unsafe_allow_html=True,
    )
    try:
        daily_index = load_daily_index()
        if not daily_index:
            st.caption('일간 리포트 데이터 없음')
        else:
            for item in daily_index[:6]:
                d  = item['date']
                ic = item['issue_count']
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1:
                    st.markdown(f'`{d}`')
                with c2:
                    if ic > 0:
                        st.markdown(
                            f'<span style="color:#EF4444;font-size:0.82rem;font-weight:600;">⚠ 이슈 {ic}개</span>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<span style="color:#10B981;font-size:0.82rem;">✓ 정상</span>',
                            unsafe_allow_html=True,
                        )
                with c3:
                    if st.button('보기', key=f'h_d_{d}', use_container_width=True):
                        st.session_state['report_date'] = d
                        st.switch_page('pages/2_일간_리포트.py')
    except Exception:
        st.caption('데이터 로딩 오류')

with col_sep:
    st.markdown(
        '<div style="width:1px;background:#E2E8F0;min-height:160px;margin-top:28px;"></div>',
        unsafe_allow_html=True,
    )

with col_weekly:
    st.markdown(
        '<div style="font-size:0.78rem;font-weight:700;letter-spacing:0.06em;'
        'color:#64748B;text-transform:uppercase;margin-bottom:8px;">📊 최근 주간 리포트</div>',
        unsafe_allow_html=True,
    )
    try:
        weekly_index = load_weekly_index()
        if not weekly_index:
            st.caption('주간 리포트 데이터 없음')
        else:
            for item in weekly_index[:4]:
                ws = item['week_start']
                we = item['week_end']
                we_short = we[5:] if len(we) >= 7 else we
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.markdown(f'`{ws}` ~ {we_short}')
                with c2:
                    if st.button('보기', key=f'h_w_{ws}', use_container_width=True):
                        st.session_state['report_week_start'] = ws
                        st.switch_page('pages/3_주간_리포트.py')
    except Exception:
        st.caption('데이터 로딩 오류')

st.divider()

# ── 최신 주간 요약 — 접이식 (fold) ──────────────────────────────────
try:
    latest_weekly = load_latest_weekly()
    if latest_weekly:
        ws_date = latest_weekly.get('week_start', '')
        we_date = latest_weekly.get('week_end', '')
        txt     = str(latest_weekly.get('ai_weekly_summary', ''))
        if txt and not txt.startswith('>'):
            with st.expander(f'🤖 최신 AI 주간 요약 — {ws_date} ~ {we_date}', expanded=False):
                st.caption('Gemini 2.5 Flash 생성 · 분석 기반 인사이트')
                st.markdown(txt)
                if ws_date:
                    st.page_link('pages/3_주간_리포트.py', label='→ 전체 주간 리포트 보기')
except Exception:
    pass

# ── 리포트 캘린더 — 날짜 탐색 보조 ──────────────────────────────────
st.subheader('📅 리포트 캘린더')
st.caption('날짜 클릭 → 해당 리포트로 이동 · **일** 이슈 리포트 · **주** 주간 리포트')

try:
    cal_data = load_calendar_data()
except Exception:
    cal_data = {}

prev_month_date = today.replace(day=1) - timedelta(days=1)
prev_y, prev_m  = prev_month_date.year, prev_month_date.month
curr_y, curr_m  = today.year, today.month

col_prev, col_curr = st.columns(2)
with col_prev:
    st.markdown(_calendar_html(prev_y, prev_m, cal_data, today), unsafe_allow_html=True)
with col_curr:
    st.markdown(_calendar_html(curr_y, curr_m, cal_data, today), unsafe_allow_html=True)
