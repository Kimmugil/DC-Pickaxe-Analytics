"""
DC-Pickaxe Analytics — 일간 이슈 리포트
정보 흐름: 헤더/메타 → KPI → 이슈 알림 → 갤러리별 이슈 상세 → 이슈 없는 갤러리 → 분석 방법론
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
    inject_css, sec_header, stat_card,
    issue_sev_class, issue_badge_class, issue_sev_label,
    methodology_daily_html,
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
    st.markdown(
        '<div style="font-size:1.0rem;font-weight:800;color:#F1F5F9;margin-bottom:4px;">⛏️ DC-Pickaxe</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button('← 캘린더로', use_container_width=True):
        st.switch_page('app.py')
    st.divider()

    # 회차 선택
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
    st.markdown(
        f'<div style="font-size:0.72rem;color:#64748B;margin-bottom:6px;">분석일: {report_date}</div>',
        unsafe_allow_html=True,
    )
    rerun_btn = st.button('현재 기준으로 다시 분석', use_container_width=True, key='btn_rerun_daily')
    if rerun_btn:
        from dashboard.analysis_runner import run_analysis_now
        with st.spinner(f'{report_date} 재분석 중...'):
            success, output = run_analysis_now(report_date)
        if success:
            st.cache_data.clear()
            st.success('재분석 완료!')
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
non_issue     = [r for r in records if str(r.get('has_issue', '0')) != '1']
issue_cnt     = len(issue_records)
total_cnt     = len(records)


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    '<div style="font-size:1.5rem;font-weight:800;color:#0F172A;line-height:1.2;margin-bottom:2px;">일간 이슈 리포트</div>'
    f'<div style="font-size:0.85rem;color:#475569;margin-bottom:16px;">'
    f'기준일: <b style="color:#0F172A">{report_date}</b>'
    f'&nbsp;·&nbsp;이슈 갤러리: <b>{issue_cnt}</b> / 전체 {total_cnt}개'
    f'{"&nbsp;·&nbsp;회차: " + sel_run if sel_run else ""}'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI ──────────────────────────────────────────────────────────────
total_24h = sum(int(r.get('new_posts_today', 0)) for r in records)
total_7d  = sum(int(r.get('new_posts_7d', 0)) for r in records)

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        stat_card(
            '24h 신규 게시글', f'{total_24h:,}건', sub='전체 갤러리 합산',
            tooltip=f'{report_date} 00:00~23:59 기준 전체 갤러리 게시글 수',
        ),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        stat_card(
            '7일 신규', f'{total_7d:,}건', sub='전체 갤러리 합산',
            tooltip=f'{report_date} 기준 이전 7일 전체 갤러리 게시글 수',
        ),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        stat_card(
            '이슈 갤러리', f'{issue_cnt}개', sub=f'전체 {total_cnt}개 중',
            tooltip='이슈 점수 3점 이상 판정 갤러리 수',
        ),
        unsafe_allow_html=True,
    )

st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

# ── 이슈 알림 배너 ───────────────────────────────────────────────────
if issue_cnt > 0:
    st.markdown(
        f'<div class="alert-banner alert-issue">'
        f'<b>{issue_cnt}개 갤러리</b>에서 이슈가 탐지되었습니다. '
        f'이슈 점수 높은 순으로 표시됩니다.'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="alert-banner alert-clear">'
        '탐지된 이슈 갤러리가 없습니다.'
        '</div>',
        unsafe_allow_html=True,
    )

# ── 이슈 갤러리 섹션 ─────────────────────────────────────────────────
if issue_records:
    st.markdown(sec_header('이슈 탐지 갤러리'), unsafe_allow_html=True)

    for result in issue_records:
        name        = result.get('gallery_name', '')
        issue_score = int(result.get('issue_score', 0))
        new_today   = int(result.get('new_posts_today', 0))
        new_7d      = int(result.get('new_posts_7d', 0))
        ai_text     = str(result.get('ai_summary', ''))
        sev_cls     = issue_sev_class(issue_score)
        bdg_cls     = issue_badge_class(issue_score)
        sev_lbl     = issue_sev_label(issue_score)
        daily_avg   = round(new_7d / 7, 1) if new_7d else 0

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

        kw_tags = ' '.join(
            f'<span class="kw-tag">{kw} <b style="color:#475569">{cnt}</b></span>'
            for kw, cnt in kw_list[:6]
        )

        # ── 갤러리 카드 헤더 ──
        st.markdown(
            f'<div class="issue-card {sev_cls}">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">'
            f'<div style="font-size:1.05rem;font-weight:800;color:#0F172A;">{name}</div>'
            f'<span class="score-badge {bdg_cls}">이슈 {sev_lbl} · 점수 {issue_score}</span>'
            f'</div>'
            f'<div style="display:flex;gap:20px;font-size:0.78rem;color:#475569;margin-bottom:10px;">'
            f'<span>24h: <b style="color:#1E293B">{new_today:,}건</b></span>'
            f'<span>7일: <b style="color:#1E293B">{new_7d:,}건</b></span>'
            f'<span>7일 일평균: <b style="color:#1E293B">{daily_avg:,.1f}건</b></span>'
            f'</div>'
            f'<div style="margin-bottom:6px;">{kw_tags}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── AI 이슈 요약 (이슈 갤러리는 기본 노출) ──
        if ai_text and not ai_text.startswith('[AI 생성 실패') and not ai_text.startswith('>'):
            st.markdown('<div class="summary-card" style="margin-bottom:8px;">', unsafe_allow_html=True)
            st.markdown(ai_text)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── TOP5 게시글 (접을 수 있는 expander) ──
        if top5:
            with st.expander(f'{name} — TOP 5 게시글 (engagement score 기준)'):
                for rank, post in enumerate(top5[:5], 1):
                    title    = post.get('제목', '')
                    link     = post.get('링크', '')
                    comments = int(post.get('댓글수', 0))
                    likes    = int(post.get('추천수', 0))
                    views    = int(post.get('조회수', 0))
                    score    = post.get('score', '')
                    date_str = str(post.get('날짜', ''))[:10]
                    title_html = (
                        f'<a href="{link}" target="_blank" '
                        f'style="color:#0F172A;text-decoration:none;border-bottom:1px solid #E2E8F0;">{title}</a>'
                        if link else title
                    )
                    st.markdown(
                        f'<div class="top-post">'
                        f'<span class="top-post-rank">{rank}</span>'
                        f'<div>'
                        f'<div class="top-post-title">{title_html}</div>'
                        f'<div class="top-post-meta">'
                        f'댓글 {comments} · 추천 {likes} · 조회 {views:,} · {date_str}'
                        f'{" · 점수 " + str(round(score, 1)) if score else ""}'
                        f'</div></div></div>',
                        unsafe_allow_html=True,
                    )

        st.markdown(
            '<hr style="border:none;border-top:1px solid #F1F5F9;margin:12px 0;">',
            unsafe_allow_html=True,
        )


# ── 이슈 없는 갤러리 요약 ────────────────────────────────────────────
if non_issue:
    with st.expander(f'이슈 없는 갤러리 ({len(non_issue)}개) — 정상 범위'):
        rows_html = ''.join(
            f'<div style="display:flex;justify-content:space-between;'
            f'align-items:center;padding:7px 0;border-bottom:1px solid #F1F5F9;font-size:0.82rem;">'
            f'<span style="color:#334155;font-weight:500;">{r.get("gallery_name","")}</span>'
            f'<span style="color:#94A3B8;">24h {int(r.get("new_posts_today",0)):,}건</span>'
            f'</div>'
            for r in non_issue
        )
        st.markdown(
            f'<div class="bento-card" style="padding:10px 16px;">{rows_html}</div>',
            unsafe_allow_html=True,
        )

# ── 분석 방법론 ───────────────────────────────────────────────────────
st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
with st.expander('분석 방법론 및 데이터 기준', expanded=False):
    st.markdown(methodology_daily_html(report_date), unsafe_allow_html=True)
