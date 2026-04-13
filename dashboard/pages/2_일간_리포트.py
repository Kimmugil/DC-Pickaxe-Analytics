"""
DC-Pickaxe Analytics — 일간 이슈 리포트
정보 흐름: 헤더 → KPI → 이슈 알림 → 갤러리별 이슈(심각도 순) → 이슈 없는 갤러리 → 방법론
모든 커스텀 HTML은 inline style 사용 (CSS 클래스 미적용 환경 대응)
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
    issue_sev_color, issue_sev_badge_style, issue_sev_label,
    kw_tag, top_post_item, methodology_daily_html,
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
st.markdown(
    '<div style="font-size:1.5rem;font-weight:800;color:#0F172A;line-height:1.2;margin-bottom:4px;">'
    '일간 이슈 리포트</div>'
    f'<div style="font-size:0.85rem;color:#64748B;margin-bottom:18px;">'
    f'기준일: <b style="color:#1E293B">{report_date}</b>'
    f'&nbsp;·&nbsp;분석 갤러리: <b style="color:#1E293B">{total_cnt}개</b>'
    f'&nbsp;·&nbsp;이슈 감지: <b style="color:#1E293B">{issue_cnt}개</b>'
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
        stat_card('24h 신규 게시글', f'{total_24h:,}건', sub='전체 갤러리 합산',
                  tooltip=f'{report_date} 00:00~23:59 기준'),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        stat_card('7일 신규', f'{total_7d:,}건', sub='전체 갤러리 합산',
                  tooltip=f'{report_date} 기준 이전 7일'),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        stat_card('이슈 갤러리', f'{issue_cnt}개', sub=f'전체 {total_cnt}개 중',
                  tooltip='이슈 점수 3점 이상 판정'),
        unsafe_allow_html=True,
    )

st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)

# ── 이슈 알림 배너 ───────────────────────────────────────────────────
if issue_cnt > 0:
    st.markdown(
        f'<div style="background:#FEF3C7;border:1px solid #F59E0B;border-radius:12px;'
        f'padding:12px 18px;margin-bottom:18px;font-size:0.88rem;font-weight:600;color:#92400E;">'
        f'이슈 {issue_cnt}개 갤러리 감지 — 이슈 점수 높은 순 표시'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="background:#F0FDF4;border:1px solid #86EFAC;border-radius:12px;'
        'padding:12px 18px;margin-bottom:18px;font-size:0.88rem;font-weight:600;color:#166534;">'
        '이슈 감지된 갤러리 없음'
        '</div>',
        unsafe_allow_html=True,
    )

# ── 이슈 갤러리 ──────────────────────────────────────────────────────
if issue_records:
    st.markdown(sec_header('이슈 탐지 갤러리'), unsafe_allow_html=True)

    for result in issue_records:
        name        = result.get('gallery_name', '')
        issue_score = int(result.get('issue_score', 0))
        new_today   = int(result.get('new_posts_today', 0))
        new_7d      = int(result.get('new_posts_7d', 0))
        ai_text     = str(result.get('ai_summary', ''))
        daily_avg   = round(new_7d / 7, 1) if new_7d else 0
        sev_col     = issue_sev_color(issue_score)
        bdg_sty     = issue_sev_badge_style(issue_score)
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

        kw_html = ' '.join(kw_tag(kw, cnt) for kw, cnt in kw_list[:6]) if kw_list else ''

        # ── 갤러리 카드 ──
        st.markdown(
            f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:16px;'
            f'padding:20px 24px;margin-bottom:8px;border-left:5px solid {sev_col};'
            f'box-shadow:0 1px 3px rgba(15,23,42,.06);">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
            f'<div style="font-size:1.1rem;font-weight:800;color:#0F172A;">{name}</div>'
            f'<span style="display:inline-flex;align-items:center;padding:3px 10px;'
            f'border-radius:20px;font-size:0.78rem;font-weight:700;{bdg_sty}">'
            f'이슈 {sev_lbl} · 점수 {issue_score}</span>'
            f'</div>'
            f'<div style="display:flex;gap:24px;font-size:0.82rem;color:#475569;margin-bottom:12px;">'
            f'<span>24h: <b style="color:#1E293B">{new_today:,}건</b></span>'
            f'<span>7일: <b style="color:#1E293B">{new_7d:,}건</b></span>'
            f'<span>7일 일평균: <b style="color:#1E293B">{daily_avg:.1f}건</b></span>'
            f'</div>'
            f'<div>{kw_html}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── AI 이슈 요약 (항상 노출) ──
        if ai_text and not ai_text.startswith('[AI 생성 실패') and not ai_text.startswith('>'):
            st.markdown(
                '<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:12px;'
                'padding:16px 20px;margin-bottom:8px;">',
                unsafe_allow_html=True,
            )
            st.markdown(ai_text)
            st.markdown('</div>', unsafe_allow_html=True)

        # ── TOP5 (expander) ──
        if top5:
            with st.expander(f'TOP 5 게시글 (engagement score 기준)'):
                for rank, post in enumerate(top5[:5], 1):
                    title    = post.get('제목', '')
                    link     = post.get('링크', '')
                    comments = int(post.get('댓글수', 0))
                    likes    = int(post.get('추천수', 0))
                    views    = int(post.get('조회수', 0))
                    date_str = str(post.get('날짜', ''))[:10]
                    title_html = (
                        f'<a href="{link}" target="_blank" '
                        f'style="color:#0F172A;text-decoration:none;border-bottom:1px solid #E2E8F0;">{title}</a>'
                        if link else title
                    )
                    st.markdown(
                        top_post_item(rank, title_html,
                                      f'댓글 {comments} · 추천 {likes} · 조회 {views:,} · {date_str}'),
                        unsafe_allow_html=True,
                    )

        st.markdown('<hr style="border:none;border-top:1px solid #F1F5F9;margin:8px 0 16px;">', unsafe_allow_html=True)


# ── 이슈 없는 갤러리 ─────────────────────────────────────────────────
if non_issue:
    with st.expander(f'이슈 없는 갤러리 ({len(non_issue)}개)'):
        rows_html = ''.join(
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:7px 0;border-bottom:1px solid #F1F5F9;font-size:0.82rem;">'
            f'<span style="color:#334155;font-weight:500;">{r.get("gallery_name","")}</span>'
            f'<span style="color:#94A3B8;">24h {int(r.get("new_posts_today",0)):,}건</span>'
            f'</div>'
            for r in non_issue
        )
        st.markdown(
            f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:12px;'
            f'padding:10px 16px;">{rows_html}</div>',
            unsafe_allow_html=True,
        )

# ── 분석 방법론 ───────────────────────────────────────────────────────
st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
with st.expander('분석 방법론 및 데이터 기준'):
    st.markdown(methodology_daily_html(report_date), unsafe_allow_html=True)
