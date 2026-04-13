"""
DC-Pickaxe Analytics — 일간 이슈 리포트 v10
변경: 분석 방법론 탭 제거 (홈에서 확인) / 사이드바 공통 nav / 경로 업데이트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='일간 이슈 리포트 — DC-Pickaxe',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import (
    inject_css, render_sidebar_nav,
    issue_sev_label, issue_sev_color, sev_badge_html, kw_tag, ai_block_html,
)
inject_css()
render_sidebar_nav()


# ── 분석 날짜 결정 ───────────────────────────────────────────────────
report_date = st.session_state.get('report_date', '')
if not report_date:
    report_date = st.query_params.get('date', '')


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all_dates() -> list[str]:
    from sheets.reader import get_available_dates
    return sorted(get_available_dates())


@st.cache_data(ttl=60)
def load_daily_data(date_str: str, run_id: str):
    from sheets.reader import get_analysis_results
    return get_analysis_results(date=date_str, run_id=run_id)


def get_run_id_for_date(date_str: str):
    from sheets.reader import get_run_ids_for_date
    ids = get_run_ids_for_date(date_str)
    return ids, ids[0] if ids else ''


# ── Prev / Next ───────────────────────────────────────────────────────
try:
    all_dates = load_all_dates()
    if report_date in all_dates:
        idx    = all_dates.index(report_date)
        prev_d = all_dates[idx - 1] if idx > 0 else None
        next_d = all_dates[idx + 1] if idx < len(all_dates) - 1 else None
    else:
        prev_d = next_d = None
except Exception:
    prev_d = next_d = None


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    run_ids, default_run = get_run_id_for_date(report_date) if report_date else ([], '')
    if len(run_ids) > 1:
        sel_run = st.selectbox(
            '분석 회차',
            options=run_ids,
            format_func=lambda x: f'{x}{"  ← 최신" if x == run_ids[0] else ""}',
            key='sel_run_daily',
        )
    else:
        sel_run = default_run
    st.divider()
    if report_date:
        st.caption(f'분석일: **{report_date}**')
    rerun_btn = st.button('다시 분석', use_container_width=True, key='btn_rerun_daily')
    if rerun_btn and report_date:
        from dashboard.analysis_runner import run_analysis_now
        with st.spinner(f'{report_date} 재분석 중...'):
            success, output = run_analysis_now(report_date)
        if success:
            st.cache_data.clear()
            st.success('완료!')
            st.rerun()
        else:
            st.error('재분석 실패')
            with st.expander('오류 로그'):
                st.code(output[:3000])
    st.divider()
    st.caption('DC-Pickaxe Analytics v10')


# ── 브레드크럼 ───────────────────────────────────────────────────────
bc1, bc2, bc3, bc4, bc5 = st.columns([0.7, 0.15, 1.2, 0.15, 5])
with bc1:
    st.page_link('app.py', label='🏠 홈')
with bc2:
    st.caption('›')
with bc3:
    st.page_link('pages/_리포트_목록.py', label='리포트 목록')
with bc4:
    st.caption('›')
with bc5:
    st.caption(f'**{report_date}** 일간 리포트' if report_date else '일간 리포트')


# ── 날짜 미지정 ───────────────────────────────────────────────────────
if not report_date:
    st.warning('날짜가 지정되지 않았습니다.')
    c1, c2 = st.columns(2)
    with c1:
        if st.button('← 홈', use_container_width=True):
            st.switch_page('app.py')
    with c2:
        if st.button('리포트 목록', use_container_width=True):
            st.switch_page('pages/_리포트_목록.py')
    st.stop()


# ── 이전/다음 날짜 내비게이션 ────────────────────────────────────────
nav_p, nav_c, nav_n = st.columns([2, 4, 2])
with nav_p:
    if prev_d:
        if st.button(f'← {prev_d}', use_container_width=True, key='nav_prev_day'):
            st.session_state['report_date'] = prev_d
            st.rerun()
with nav_c:
    st.markdown(
        f'<div style="text-align:center;font-size:0.82rem;color:#94A3B8;padding-top:6px;">'
        f'{report_date}</div>',
        unsafe_allow_html=True,
    )
with nav_n:
    if next_d:
        if st.button(f'{next_d} →', use_container_width=True, key='nav_next_day'):
            st.session_state['report_date'] = next_d
            st.rerun()

st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)


# ── 데이터 로드 ──────────────────────────────────────────────────────
try:
    results_df = load_daily_data(report_date, sel_run)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()

if results_df.empty:
    st.warning(f'**{report_date}** 분석 결과가 없습니다.')
    if st.button('← 리포트 목록으로'):
        st.switch_page('pages/_리포트_목록.py')
    st.stop()

records       = results_df.to_dict('records')
issue_records = sorted(
    [r for r in records if str(r.get('has_issue', '0')) == '1'],
    key=lambda r: int(r.get('issue_score', 0)),
    reverse=True,
)
non_issue = [r for r in records if str(r.get('has_issue', '0')) != '1']
issue_cnt = len(issue_records)
total_cnt = len(records)

# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.title('일간 이슈 리포트')
st.caption(
    f'기준일: **{report_date}** · 분석 갤러리: **{total_cnt}개** · '
    f'이슈 감지: **{issue_cnt}개**'
    + (f' · 회차: {sel_run}' if sel_run else '')
)

# ── KPI ──────────────────────────────────────────────────────────────
total_24h = sum(int(r.get('new_posts_today', 0)) for r in records)
total_7d  = sum(int(r.get('new_posts_7d', 0)) for r in records)
daily_avg = round(total_7d / 7, 1) if total_7d else 0
delta_val = round(total_24h - daily_avg, 1)

k1, k2, k3 = st.columns(3)
with k1:
    st.metric('24H 신규 게시글', f'{total_24h:,}건',
              delta=f'{delta_val:+.0f} vs 7일 평균', delta_color='normal',
              help=f'{report_date} 전체 합산 / 7일 일평균 {daily_avg:.1f}건 대비')
with k2:
    st.metric('7일 신규', f'{total_7d:,}건')
with k3:
    st.metric('이슈 갤러리', f'{issue_cnt}개',
              help=f'전체 {total_cnt}개 중 이슈 점수 3점 이상')

# ── 갤러리별 24h 차트 ─────────────────────────────────────────────────
try:
    from dashboard.components.trend_charts import render_multi_gallery_trend
    render_multi_gallery_trend(records, title='갤러리별 24H 신규 게시글')
except Exception:
    pass

# ── 이슈 알림 배너 ───────────────────────────────────────────────────
if issue_cnt > 0:
    st.warning(f'이슈 {issue_cnt}개 갤러리 감지 — 이슈 점수 높은 순')
else:
    st.success('이슈 감지된 갤러리 없음 ✓')

# ── 이슈 갤러리 카드 ─────────────────────────────────────────────────
if issue_records:
    st.subheader('이슈 탐지 갤러리')
    for result in issue_records:
        name        = result.get('gallery_name', '')
        issue_score = int(result.get('issue_score', 0))
        new_today   = int(result.get('new_posts_today', 0))
        new_7d      = int(result.get('new_posts_7d', 0))
        ai_text     = str(result.get('ai_summary', ''))
        daily_avg_g = round(new_7d / 7, 1) if new_7d else 0
        delta_g     = round(new_today - daily_avg_g, 1)
        sev_col     = issue_sev_color(issue_score)

        kw_raw = result.get('top_keywords', '[]')
        if isinstance(kw_raw, str):
            try:
                kw_list = json.loads(kw_raw)
            except Exception:
                kw_list = []
        else:
            kw_list = kw_raw or []

        top5_raw = result.get('top5_posts', '[]')
        if isinstance(top5_raw, str):
            try:
                top5 = json.loads(top5_raw)
            except Exception:
                top5 = []
        else:
            top5 = top5_raw or []

        st.markdown(
            f'<div style="height:5px;background:{sev_col};border-radius:3px;margin-bottom:1px;"></div>',
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            col_name, col_badge = st.columns([3, 1])
            with col_name:
                st.markdown(f'**{name}**')
            with col_badge:
                st.markdown(sev_badge_html(issue_score), unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            c1.metric('24H 게시글', f'{new_today:,}건',
                      delta=f'{delta_g:+.0f} vs 일평균', delta_color='normal')
            c2.metric('7일 게시글', f'{new_7d:,}건')
            c3.metric('7일 일평균', f'{daily_avg_g:.1f}건')
            if kw_list:
                st.markdown(
                    ' '.join(kw_tag(kw, cnt) for kw, cnt in kw_list[:6]),
                    unsafe_allow_html=True,
                )
            if ai_text and not ai_text.startswith('[AI 생성 실패') and not ai_text.startswith('>'):
                st.markdown(ai_block_html(ai_text, 'AI 이슈 요약'), unsafe_allow_html=True)
            if top5:
                with st.expander('TOP 5 게시글 (Engagement Score 기준)'):
                    for rank, post in enumerate(top5[:5], 1):
                        title    = post.get('제목', '')
                        link     = post.get('링크', '')
                        comments = int(post.get('댓글수', 0))
                        likes    = int(post.get('추천수', 0))
                        views    = int(post.get('조회수', 0))
                        date_str = str(post.get('날짜', ''))[:10]
                        t_disp   = f'[{title}]({link})' if link else title
                        st.markdown(
                            f'**{rank}.** {t_disp}  \n'
                            f'💬 {comments} &nbsp;👍 {likes} &nbsp;👁 {views:,} &nbsp;· {date_str}'
                        )

# ── 이슈 없는 갤러리 인라인 ──────────────────────────────────────────
if non_issue:
    st.divider()
    st.caption(f'**이슈 없는 갤러리 ({len(non_issue)}개)** — 정상 범위')
    items_html = '&nbsp;&nbsp;|&nbsp;&nbsp;'.join(
        f'<b>{r.get("gallery_name", "")}</b>'
        f'&nbsp;<span style="color:#94A3B8;font-size:0.8rem;">'
        f'{int(r.get("new_posts_today", 0)):,}건</span>'
        for r in non_issue
    )
    st.markdown(
        f'<div style="font-size:0.85rem;color:#475569;line-height:2;">{items_html}</div>',
        unsafe_allow_html=True,
    )
