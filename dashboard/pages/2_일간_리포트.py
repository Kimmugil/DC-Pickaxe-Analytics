"""
DC-Pickaxe Analytics — 일간 이슈 리포트 v7
정보 흐름: 헤더 → KPI → 이슈 알림 → 갤러리별 이슈(심각도 순) → 이슈 없는 갤러리
탭 구조: [📋 이슈 리포트] [🔍 분석 방법론]
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
    inject_css, issue_sev_label, issue_sev_color, kw_tag,
    METHODOLOGY_DAILY_TEMPLATE,
)
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
@st.cache_data(ttl=60)
def load_daily_data(date_str: str, run_id: str):
    from sheets.reader import get_analysis_results
    return get_analysis_results(date=date_str, run_id=run_id)


def get_run_id_for_date(date_str: str) -> tuple[list[str], str]:
    from sheets.reader import get_run_ids_for_date
    ids = get_run_ids_for_date(date_str)
    return ids, ids[0] if ids else ''


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('**⛏️ DC-Pickaxe**')
    st.divider()
    if st.button('← 캘린더로', use_container_width=True):
        st.switch_page('app.py')
    st.divider()

    run_ids, default_run = get_run_id_for_date(report_date)
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
    st.caption(f'분석일: {report_date}')
    rerun_btn = st.button('현재 기준으로 다시 분석', use_container_width=True, key='btn_rerun_daily')
    if rerun_btn:
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


# ── 데이터 로드 ──────────────────────────────────────────────────────
try:
    results_df = load_daily_data(report_date, sel_run)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()

if results_df.empty:
    st.warning(f'**{report_date}** 분석 결과가 없습니다.')
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

# ── 탭 구조 ──────────────────────────────────────────────────────────
tab_report, tab_method = st.tabs(['📋 이슈 리포트', '🔍 분석 방법론'])

with tab_report:
    # ── KPI
    total_24h = sum(int(r.get('new_posts_today', 0)) for r in records)
    total_7d  = sum(int(r.get('new_posts_7d', 0)) for r in records)

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric('24h 신규 게시글', f'{total_24h:,}건',
                  help=f'{report_date} 00:00~23:59 전체 갤러리 합산')
    with k2:
        st.metric('7일 신규', f'{total_7d:,}건',
                  help=f'{report_date} 기준 이전 7일 전체 갤러리 합산')
    with k3:
        st.metric('이슈 갤러리', f'{issue_cnt}개',
                  help=f'전체 {total_cnt}개 중 이슈 점수 3점 이상')

    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

    # ── 이슈 알림 배너
    if issue_cnt > 0:
        st.warning(f'이슈 {issue_cnt}개 갤러리 감지 — 이슈 점수 높은 순 표시')
    else:
        st.success('이슈 감지된 갤러리 없음')

    # ── 이슈 갤러리
    if issue_records:
        st.subheader('이슈 탐지 갤러리')

        for result in issue_records:
            name        = result.get('gallery_name', '')
            issue_score = int(result.get('issue_score', 0))
            new_today   = int(result.get('new_posts_today', 0))
            new_7d      = int(result.get('new_posts_7d', 0))
            ai_text     = str(result.get('ai_summary', ''))
            daily_avg   = round(new_7d / 7, 1) if new_7d else 0
            sev_col     = issue_sev_color(issue_score)
            sev_lbl     = issue_sev_label(issue_score)

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

            # 심각도 색상 바 (inline style — 항상 렌더링됨)
            st.markdown(
                f'<div style="height:4px;background:{sev_col};border-radius:2px;margin-bottom:2px;"></div>',
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                # 헤더: 갤러리명 + 심각도 배지
                col_name, col_badge = st.columns([3, 1])
                with col_name:
                    st.markdown(f'### {name}')
                with col_badge:
                    badge_label = f'이슈 {sev_lbl} · {issue_score}점'
                    if issue_score >= 7:
                        st.error(badge_label)
                    elif issue_score >= 4:
                        st.warning(badge_label)
                    else:
                        st.info(badge_label)

                # 통계
                c1, c2, c3 = st.columns(3)
                c1.metric('24h 게시글', f'{new_today:,}건')
                c2.metric('7일 게시글', f'{new_7d:,}건')
                c3.metric('7일 일평균', f'{daily_avg:.1f}건')

                # 키워드 태그 (inline style 사용 — 항상 렌더링됨)
                if kw_list:
                    kw_html = ' '.join(kw_tag(kw, cnt) for kw, cnt in kw_list[:6])
                    st.markdown(kw_html, unsafe_allow_html=True)

                # AI 이슈 요약
                if ai_text and not ai_text.startswith('[AI 생성 실패') and not ai_text.startswith('>'):
                    st.markdown('**AI 이슈 요약**')
                    st.markdown(ai_text)

                # TOP5 게시글
                if top5:
                    with st.expander('TOP 5 게시글 (engagement score 기준)'):
                        for rank, post in enumerate(top5[:5], 1):
                            title    = post.get('제목', '')
                            link     = post.get('링크', '')
                            comments = int(post.get('댓글수', 0))
                            likes    = int(post.get('추천수', 0))
                            views    = int(post.get('조회수', 0))
                            date_str = str(post.get('날짜', ''))[:10]
                            title_display = (
                                f'[{title}]({link})' if link else title
                            )
                            st.markdown(
                                f'**{rank}.** {title_display}  \n'
                                f'댓글 {comments} · 추천 {likes} · 조회 {views:,} · {date_str}'
                            )

    # ── 이슈 없는 갤러리
    if non_issue:
        with st.expander(f'이슈 없는 갤러리 ({len(non_issue)}개)'):
            for r in non_issue:
                st.markdown(
                    f'**{r.get("gallery_name", "")}** — '
                    f'24h {int(r.get("new_posts_today", 0)):,}건'
                )


with tab_method:
    st.markdown(METHODOLOGY_DAILY_TEMPLATE.format(date=report_date))
