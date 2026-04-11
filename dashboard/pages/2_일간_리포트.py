"""
DC-Pickaxe Analytics — 일간 이슈 리포트
이슈가 탐지된 날짜의 갤러리별 이슈 내용을 표시합니다.
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

from dashboard.dash_styles import inject_css, sec_header, stat_card
inject_css()


# ── 분석 날짜 결정 ───────────────────────────────────────────────────
report_date = st.session_state.get('report_date', '')
if not report_date:
    report_date = st.query_params.get('date', '')

if not report_date:
    st.warning('날짜가 지정되지 않았습니다. 메인 캘린더에서 날짜를 선택해주세요.')
    if st.button('← 메인으로'):
        st.switch_page('app.py')
    st.stop()


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_daily_data(date: str):
    from sheets.reader import get_analysis_results, get_run_ids_for_date
    run_ids = get_run_ids_for_date(date)
    run_id  = run_ids[0] if run_ids else None
    df      = get_analysis_results(date=date, run_id=run_id)
    return df, run_id


try:
    results_df, run_id = load_daily_data(report_date)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.0rem;font-weight:800;color:#0A0A0A;margin-bottom:4px;">'
        '⛏️ DC-Pickaxe</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button('← 캘린더로 돌아가기', use_container_width=True):
        st.switch_page('app.py')

    if not results_df.empty:
        # 회차 선택
        from sheets.reader import get_run_ids_for_date
        run_ids = get_run_ids_for_date(report_date)
        if len(run_ids) > 1:
            st.divider()
            sel_run = st.selectbox(
                '분석 회차',
                options=run_ids,
                format_func=lambda x, ids=run_ids: f'{x}{"  ← 최신" if x == ids[0] else ""}',
                key='sel_run_daily',
            )
            if sel_run != run_id:
                st.session_state['_daily_run_override'] = sel_run
                st.rerun()

    st.divider()
    st.markdown(
        f'<div style="font-size:0.72rem;color:#888888;">분석일: {report_date}</div>',
        unsafe_allow_html=True,
    )


# ── 회차 오버라이드 처리 ─────────────────────────────────────────────
if '_daily_run_override' in st.session_state:
    override_run = st.session_state.pop('_daily_run_override')
    try:
        from sheets.reader import get_analysis_results
        results_df = get_analysis_results(date=report_date, run_id=override_run)
        run_id = override_run
    except Exception:
        pass


# ── 데이터 없음 처리 ─────────────────────────────────────────────────
if results_df.empty:
    st.warning(f'**{report_date}** 분석 결과가 없습니다.')
    st.stop()


# ── 이슈 갤러리 필터 ─────────────────────────────────────────────────
records = results_df.to_dict('records')
issue_records = [r for r in records if str(r.get('has_issue', '0')) == '1']
all_records   = records


# ── 페이지 헤더 ──────────────────────────────────────────────────────
issue_cnt = len(issue_records)
total_cnt = len(all_records)
run_txt   = f'회차: {run_id}' if run_id else ''

st.markdown(
    f'<div style="font-size:1.4rem;font-weight:800;color:#0A0A0A;margin-bottom:4px;">'
    f'일간 이슈 리포트</div>'
    f'<div style="font-size:0.85rem;color:#555555;margin-bottom:20px;">'
    f'기준일: <b style="color:#0A0A0A">{report_date}</b>'
    f'&nbsp;·&nbsp;이슈 갤러리: <b>{issue_cnt}</b> / 전체 {total_cnt}개'
    f'{"&nbsp;·&nbsp;" + run_txt if run_txt else ""}</div>',
    unsafe_allow_html=True,
)

# ── KPI ──────────────────────────────────────────────────────────────
total_24h = sum(int(r.get('new_posts_today', 0)) for r in all_records)
total_7d  = sum(int(r.get('new_posts_7d', 0)) for r in all_records)

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        stat_card('24h 전체 신규', f'{total_24h:,}건', sub='전체 갤러리 합산'),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        stat_card('7일 신규', f'{total_7d:,}건', sub='전체 갤러리 합산'),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        stat_card('이슈 갤러리', f'{issue_cnt}개', sub=f'전체 {total_cnt}개 중'),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── 이슈 갤러리 섹션 ─────────────────────────────────────────────────
if not issue_records:
    st.info(f'{report_date}에는 이슈가 탐지된 갤러리가 없습니다.')
else:
    st.markdown(sec_header('이슈 탐지 갤러리'), unsafe_allow_html=True)

    for result in issue_records:
        name        = result.get('gallery_name', '')
        issue_score = int(result.get('issue_score', 0))
        new_today   = int(result.get('new_posts_today', 0))
        new_7d      = int(result.get('new_posts_7d', 0))
        ai_text     = str(result.get('ai_summary', ''))

        # 키워드
        kw_raw = result.get('top_keywords', '[]')
        if isinstance(kw_raw, str):
            try:
                kw_list = json.loads(kw_raw)
            except Exception:
                kw_list = []
        else:
            kw_list = kw_raw or []

        # TOP5
        top5_raw = result.get('top5_posts', '[]')
        if isinstance(top5_raw, str):
            try:
                top5 = json.loads(top5_raw)
            except Exception:
                top5 = []
        else:
            top5 = top5_raw or []

        # 갤러리 섹션 렌더링
        kw_tags = ' '.join(
            f'<span class="kw-tag">{kw} <b style="color:#555555">{cnt}</b></span>'
            for kw, cnt in kw_list[:5]
        )

        st.markdown(
            f'<div class="lc" style="border-left:4px solid #0A0A0A;">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
            f'<div style="font-size:1.05rem;font-weight:800;color:#0A0A0A;">{name}</div>'
            f'<span class="issue-badge">이슈 점수 {issue_score}</span>'
            f'</div>'
            f'<div style="font-size:0.78rem;color:#555555;margin-bottom:10px;">'
            f'24h {new_today:,}건 &nbsp;·&nbsp; 7일 {new_7d:,}건'
            f'</div>'
            f'<div style="margin-bottom:10px;">{kw_tags}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # AI 이슈 요약
        if ai_text and not ai_text.startswith('[AI 생성 실패'):
            with st.expander(f'{name} — AI 이슈 요약', expanded=True):
                st.markdown(ai_text)
        elif ai_text:
            st.caption(ai_text)

        # TOP5 게시글
        if top5:
            st.markdown(
                f'<div style="font-size:0.8rem;font-weight:700;color:#0A0A0A;'
                f'margin:6px 0 8px;">TOP 5 게시글</div>',
                unsafe_allow_html=True,
            )
            for rank, post in enumerate(top5[:5], 1):
                title   = post.get('제목', '')
                link    = post.get('링크', '')
                comments = int(post.get('댓글수', 0))
                likes    = int(post.get('추천수', 0))
                views    = int(post.get('조회수', 0))
                date_str = str(post.get('날짜', ''))[:10]

                title_html = (
                    f'<a href="{link}" target="_blank" '
                    f'style="color:#0A0A0A;text-decoration:none;">{title}</a>'
                    if link else title
                )

                st.markdown(
                    f'<div class="top-post">'
                    f'<span class="top-post-rank">{rank}</span>'
                    f'<div>'
                    f'<div class="top-post-title">{title_html}</div>'
                    f'<div class="top-post-meta">'
                    f'댓글 {comments} · 추천 {likes} · 조회 {views:,} · {date_str}'
                    f'</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr style="border:none;border-top:1px solid #EEEEEE;margin:14px 0;">', unsafe_allow_html=True)


# ── 이슈 없는 갤러리 요약 ────────────────────────────────────────────
non_issue = [r for r in all_records if str(r.get('has_issue', '0')) != '1']
if non_issue:
    with st.expander(f'이슈 없는 갤러리 ({len(non_issue)}개)'):
        rows_html = ''.join(
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:6px 0;border-bottom:1px solid #F0F0F0;font-size:0.82rem;">'
            f'<span style="color:#333333;">{r.get("gallery_name","")}</span>'
            f'<span style="color:#888888;">24h {int(r.get("new_posts_today",0)):,}건</span>'
            f'</div>'
            for r in non_issue
        )
        st.markdown(
            f'<div class="lc" style="padding:10px 16px;">{rows_html}</div>',
            unsafe_allow_html=True,
        )
