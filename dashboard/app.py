"""
DC-Pickaxe Analytics — 홈 v10
구성:
  - 통계 카드 (디씨곡괭이 감시탑 스타일)
  - 최신 AI 주간 요약 (확장, 헤딩 크기 축소)
  - 최신 일간 이슈 요약 (이슈 있을 때만)
  - 리포트 캘린더 (발행 주기 안내 포함)
  - 분석 방법론 (expander)
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

from dashboard.dash_styles import (
    inject_css, render_sidebar_nav, shrink_headings,
    METHODOLOGY_DAILY_TEMPLATE, METHODOLOGY_WEEKLY_TEMPLATE,
)
inject_css()

# ── 캘린더 클릭 네비게이션 ──────────────────────────────────────────
params = st.query_params
if 'nav_date' in params:
    nav_date = params['nav_date']
    nav_type = params.get('nav_type', 'daily')
    st.session_state['report_date'] = nav_date
    if nav_type == 'weekly':
        st.session_state['report_week_start'] = nav_date
        st.switch_page('pages/_주간_리포트.py')
    else:
        st.switch_page('pages/_일간_리포트.py')


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_overall_stats():
    from sheets.reader import get_latest_overall_stats
    return get_latest_overall_stats()


@st.cache_data(ttl=300)
def load_latest_weekly():
    from sheets.reader import get_latest_weekly_summary
    return get_latest_weekly_summary()


@st.cache_data(ttl=300)
def load_daily_index():
    from sheets.reader import get_daily_report_index
    return get_daily_report_index()


@st.cache_data(ttl=300)
def load_calendar_data():
    from sheets.reader import get_calendar_data
    return get_calendar_data()


def _relative_date(date_str: str) -> str:
    try:
        d    = date.fromisoformat(date_str)
        diff = (date.today() - d).days
        if diff == 0:
            return '오늘'
        elif diff == 1:
            return '어제'
        else:
            return f'{diff}일 전'
    except Exception:
        return date_str


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
render_sidebar_nav()

with st.sidebar:
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
    st.caption('DC-Pickaxe Analytics v10')


# ── 데이터 로드 ──────────────────────────────────────────────────────
today = date.today()
try:
    overall = load_overall_stats()
except Exception:
    overall = {}
try:
    daily_idx = load_daily_index()
except Exception:
    daily_idx = []


# ── 페이지 타이틀 ─────────────────────────────────────────────────────
st.title('⛏️ DC-Pickaxe Analytics')
st.caption('키우기 장르 갤러리 자동 분석 대시보드')

st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)

# ── 통계 카드 ─────────────────────────────────────────────────────────
last_date   = overall.get('date', '-')
total_posts = overall.get('total_posts', 0)
new_today   = overall.get('new_posts_today', 0)
rel_time    = _relative_date(last_date)

k1, k2, k3 = st.columns(3)
with k1:
    st.metric('총 수집 게시글', f'{total_posts:,}건',
              help='전체 갤러리 누적 수집 합산')
with k2:
    st.metric('24H 신규 수집', f'{new_today:,}건',
              help=f'{last_date} 00:00~23:59 수집량')
with k3:
    st.metric('마지막 분석', rel_time,
              help=f'분석 기준일: {last_date}')

st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
st.link_button(
    '🔗 디씨곡괭이 감시탑 바로가기',
    'https://kimmugil-dc-pickaxe-dashboard.streamlit.app/',
    use_container_width=False,
)

st.divider()

# ── 최신 AI 주간 요약 (EXPANDED) ─────────────────────────────────────
try:
    latest_weekly = load_latest_weekly()
    if latest_weekly:
        ws_date = latest_weekly.get('week_start', '')
        we_date = latest_weekly.get('week_end', '')
        txt     = str(latest_weekly.get('ai_weekly_summary', ''))
        col_hdr, col_link = st.columns([5, 1])
        with col_hdr:
            st.subheader('최신 AI 주간 요약')
            st.caption(f'분석 기간: **{ws_date} ~ {we_date}** · Gemini 2.5 Flash 생성')
        with col_link:
            if ws_date:
                if st.button('전체 보기 →', key='btn_weekly_full'):
                    st.session_state['report_week_start'] = ws_date
                    st.switch_page('pages/_주간_리포트.py')
        if txt and not txt.startswith('>'):
            with st.container(border=True):
                st.markdown(shrink_headings(txt))
        else:
            st.info('주간 요약 데이터가 없습니다.')
    else:
        st.info('주간 요약 데이터가 없습니다.')
except Exception:
    st.info('주간 요약 데이터를 불러올 수 없습니다.')

st.divider()

# ── 최신 일간 이슈 요약 (이슈 있을 때만) ─────────────────────────────
try:
    issue_items = [item for item in daily_idx if item.get('issue_count', 0) > 0]
    if issue_items:
        latest_issue = issue_items[0]
        d_str = latest_issue['date']
        ic    = latest_issue['issue_count']
        col_hdr2, col_link2 = st.columns([5, 1])
        with col_hdr2:
            st.subheader('최신 일간 이슈 요약')
            st.caption(
                f'기준일: **{d_str}** · 이슈 감지 갤러리: **{ic}개** · '
                f'일간 리포트는 이슈 감지 시에만 발행됩니다.'
            )
        with col_link2:
            if st.button('보기 →', key='btn_daily_full'):
                st.session_state['report_date'] = d_str
                st.switch_page('pages/_일간_리포트.py')
        try:
            from sheets.reader import get_analysis_results
            df = get_analysis_results(date=d_str)
            if not df.empty:
                records = df.to_dict('records')
                issues  = sorted(
                    [r for r in records if str(r.get('has_issue', '0')) == '1'],
                    key=lambda r: int(r.get('issue_score', 0)),
                    reverse=True,
                )
                if issues:
                    with st.container(border=True):
                        for r in issues:
                            name  = r.get('gallery_name', '')
                            score = r.get('issue_score', 0)
                            ai_t  = str(r.get('ai_summary', ''))
                            from dashboard.dash_styles import sev_badge_html, shrink_headings
                            col_n, col_b = st.columns([3, 1])
                            with col_n:
                                st.markdown(f'**{name}**')
                            with col_b:
                                st.markdown(sev_badge_html(int(score)), unsafe_allow_html=True)
                            if ai_t and not ai_t.startswith('[AI 생성 실패') and not ai_t.startswith('>'):
                                st.markdown(shrink_headings(ai_t))
                            st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
        except Exception:
            pass
        st.divider()
except Exception:
    pass

# ── 리포트 캘린더 ─────────────────────────────────────────────────────
st.subheader('📅 리포트 캘린더')
st.markdown(
    '<div style="background:#F1F5F9;border-radius:10px;padding:10px 14px;'
    'font-size:0.83rem;color:#475569;margin-bottom:12px;line-height:1.6;">'
    '📊&nbsp;<b>주간 리포트</b>: 매주 <b>월요일</b> 정기 발행&nbsp;&nbsp;·&nbsp;&nbsp;'
    '📋&nbsp;<b>일간 리포트</b>: 이슈 감지 시에만 발행 (특이 동향 없으면 미발행)'
    '</div>',
    unsafe_allow_html=True,
)

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

# ── 분석 방법론 ───────────────────────────────────────────────────────
st.divider()
with st.expander('🔍 분석 방법론', expanded=False):
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.markdown('**📋 일간 이슈 리포트 방법론**')
        st.markdown(METHODOLOGY_DAILY_TEMPLATE.format(date='(해당 분석일)'))
    with col_m2:
        st.markdown('**📊 주간 분석 리포트 방법론**')
        st.markdown(METHODOLOGY_WEEKLY_TEMPLATE.format(
            week_start='(주 시작일)',
            week_end='(주 종료일)',
        ))
