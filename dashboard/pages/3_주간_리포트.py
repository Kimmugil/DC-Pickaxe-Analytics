"""
DC-Pickaxe Analytics — 주간 분석 리포트
AI 종합 요약 + 갤러리별 TOP5 + 키워드 (2열 레이아웃)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='주간 분석 리포트 — DC-Pickaxe',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, sec_header, stat_card, gallery_color
inject_css()


# ── 주 시작일 결정 ───────────────────────────────────────────────────
week_start = st.session_state.get('report_week_start', '')
if not week_start:
    week_start = st.query_params.get('week_start', '')

if not week_start:
    st.warning('주 시작일이 지정되지 않았습니다. 메인 캘린더에서 날짜를 선택해주세요.')
    if st.button('← 메인으로'):
        st.switch_page('app.py')
    st.stop()


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_weekly_data(ws: str, run_id: str = None):
    from sheets.reader import get_weekly_gallery_results, get_weekly_summary
    gallery_df = get_weekly_gallery_results(ws, run_id=run_id)
    summary_df = get_weekly_summary(ws)
    return gallery_df, summary_df


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.0rem;font-weight:800;color:#F1F5F9;margin-bottom:4px;">'
        '⛏️ DC-Pickaxe</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    if st.button('← 캘린더로', use_container_width=True):
        st.switch_page('app.py')

    st.divider()

    # 주 선택
    try:
        from sheets.reader import get_available_weekly_starts, get_weekly_run_ids
        weekly_starts = get_available_weekly_starts()
        if weekly_starts and len(weekly_starts) > 1:
            sel_ws = st.selectbox(
                '주 선택',
                options=weekly_starts,
                index=weekly_starts.index(week_start) if week_start in weekly_starts else 0,
                key='sel_week_start',
            )
            if sel_ws != week_start:
                st.session_state['report_week_start'] = sel_ws
                st.session_state.pop('report_weekly_run_id', None)
                st.rerun()
    except Exception:
        pass

    # run_id 선택
    try:
        weekly_run_ids = get_weekly_run_ids(week_start)
    except Exception:
        weekly_run_ids = []

    selected_run_id = st.session_state.get('report_weekly_run_id',
                                            weekly_run_ids[0] if weekly_run_ids else None)

    if len(weekly_run_ids) > 1:
        sel_rid = st.selectbox(
            '분석 회차',
            options=weekly_run_ids,
            format_func=lambda x: f'{x}{"  ← 최신" if x == weekly_run_ids[0] else ""}',
            key='sel_weekly_run',
        )
        if sel_rid != selected_run_id:
            st.session_state['report_weekly_run_id'] = sel_rid
            st.rerun()
    else:
        sel_rid = selected_run_id

    st.divider()

    # 재분석 버튼
    st.markdown(
        f'<div style="font-size:0.72rem;color:#64748B;margin-bottom:6px;">'
        f'주: {week_start}</div>',
        unsafe_allow_html=True,
    )
    rerun_btn = st.button('현재 기준으로 다시 분석', use_container_width=True, key='btn_rerun_weekly')
    if rerun_btn:
        from dashboard.analysis_runner import run_weekly_now
        with st.spinner(f'{week_start} 주간 재분석 중...'):
            success, output = run_weekly_now(week_start)
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
    gallery_df, summary_df = load_weekly_data(week_start, sel_rid)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()

if gallery_df.empty:
    st.warning(f'**{week_start}** 주간 분석 결과가 없습니다.')
    st.stop()

gallery_records = gallery_df.to_dict('records')
week_end = ''
if not summary_df.empty:
    week_end = str(summary_df.iloc[-1].get('week_end', ''))
elif gallery_records:
    week_end = str(gallery_records[0].get('week_end', ''))


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-size:1.4rem;font-weight:800;color:#0F172A;margin-bottom:4px;">'
    f'주간 분석 리포트</div>'
    f'<div style="font-size:0.85rem;color:#475569;margin-bottom:20px;">'
    f'<b style="color:#0F172A">{week_start}</b> ~ '
    f'<b style="color:#0F172A">{week_end}</b>'
    f'&nbsp;·&nbsp;갤러리 {len(gallery_records)}개'
    f'{"&nbsp;·&nbsp;회차: " + (sel_rid or "") if sel_rid else ""}</div>',
    unsafe_allow_html=True,
)

# ── KPI ──────────────────────────────────────────────────────────────
total_posts_week = sum(int(r.get('total_posts_week', 0)) for r in gallery_records)
most_active      = max(gallery_records, key=lambda r: int(r.get('total_posts_week', 0)), default={})
avg_posts        = int(total_posts_week / len(gallery_records)) if gallery_records else 0

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        stat_card('주간 전체 게시글', f'{total_posts_week:,}건',
                  sub='전체 갤러리 합산',
                  tooltip='해당 주 월~일 전체 갤러리 게시글 수'),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        stat_card('가장 활발한 갤러리',
                  most_active.get('gallery_name', '-'),
                  sub=f'{int(most_active.get("total_posts_week", 0)):,}건'),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        stat_card('갤러리당 평균', f'{avg_posts:,}건', sub='주간 평균'),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── AI 종합 요약 (st.markdown으로 직접 렌더링) ────────────────────────
st.markdown(sec_header('주간 종합 요약'), unsafe_allow_html=True)

if not summary_df.empty:
    # 가장 최신 run_id의 요약 사용
    latest_row = summary_df.iloc[-1]
    summary_text = str(latest_row.get('ai_weekly_summary', ''))
    if summary_text and not summary_text.startswith('>'):
        # 마크다운 직접 렌더링 (**, ##, [링크](URL) 정상 표시)
        st.markdown(
            '<div class="weekly-card" style="margin-bottom:0">',
            unsafe_allow_html=True,
        )
        st.markdown(summary_text)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info('종합 요약이 없습니다.')
else:
    st.info('종합 요약 데이터가 없습니다.')

st.markdown('')

# ── 갤러리별 상세 (2열 레이아웃) ─────────────────────────────────────
st.markdown(sec_header('갤러리별 상세'), unsafe_allow_html=True)

# 2개씩 컬럼으로 배치
pairs = [gallery_records[i:i+2] for i in range(0, len(gallery_records), 2)]

for pair in pairs:
    cols = st.columns(2)
    for col, result in zip(cols, pair):
        with col:
            name      = result.get('gallery_name', '')
            total     = int(result.get('total_posts_week', 0))
            ai_weekly = str(result.get('ai_gallery_weekly', ''))
            color     = gallery_color(gallery_records.index(result))

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
                for kw, cnt in kw_list[:5]
            ) or '<span style="color:#94A3B8;font-size:0.78rem;">키워드 없음</span>'

            # 갤러리 헤더 카드
            st.markdown(
                f'<div class="lc" style="border-top:3px solid {color};padding-bottom:10px;">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
                f'<div style="font-size:1.0rem;font-weight:800;color:#0F172A;">{name}</div>'
                f'<div style="font-size:0.78rem;color:#94A3B8;margin-left:auto;">'
                f'주간 {total:,}건</div>'
                f'</div>'
                f'<div style="margin-bottom:10px;">{kw_tags}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # AI 주간 갤러리 요약
            if ai_weekly and not ai_weekly.startswith('>'):
                with st.expander(f'{name} — AI 주간 요약'):
                    st.markdown(ai_weekly)

            # TOP5 게시글
            if top5:
                for rank, post in enumerate(top5[:5], 1):
                    title    = post.get('제목', '')
                    link     = post.get('링크', '')
                    comments = int(post.get('댓글수', 0))
                    likes    = int(post.get('추천수', 0))
                    views    = int(post.get('조회수', 0))
                    date_str = str(post.get('날짜', ''))[:10]
                    title_html = (
                        f'<a href="{link}" target="_blank" '
                        f'style="color:#0F172A;text-decoration:none;'
                        f'border-bottom:1px solid #E2E8F0;">{title}</a>'
                        if link else title
                    )
                    st.markdown(
                        f'<div class="top-post">'
                        f'<span class="top-post-rank">{rank}</span>'
                        f'<div>'
                        f'<div class="top-post-title">{title_html}</div>'
                        f'<div class="top-post-meta">'
                        f'댓글 {comments} · 추천 {likes} · 조회 {views:,} · {date_str}'
                        f'</div></div></div>',
                        unsafe_allow_html=True,
                    )

    # 홀수 개일 때 오른쪽 빈 컬럼 처리 (st.columns이 이미 빈 컬럼 채움)
