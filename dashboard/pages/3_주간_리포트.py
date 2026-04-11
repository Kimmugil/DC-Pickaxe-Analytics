"""
DC-Pickaxe Analytics — 주간 분석 리포트
정규화 추이 차트 + 갤러리별 TOP5 + 키워드 + AI 종합 요약
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

from dashboard.dash_styles import inject_css, sec_header, stat_card, cross_card, gallery_color
from dashboard.svg_charts import multiline, wrap
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
@st.cache_data(ttl=300)
def load_weekly_data(ws: str, run_id: str = None):
    from sheets.reader import get_weekly_gallery_results, get_weekly_summary
    gallery_df = get_weekly_gallery_results(ws, run_id=run_id)
    summary_df = get_weekly_summary(ws)
    return gallery_df, summary_df


try:
    from sheets.reader import get_weekly_run_ids
    weekly_run_ids = get_weekly_run_ids(week_start)
    selected_run_id = st.session_state.get('report_weekly_run_id', weekly_run_ids[0] if weekly_run_ids else None)
    gallery_df, summary_df = load_weekly_data(week_start, selected_run_id)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    weekly_run_ids = []
    selected_run_id = None
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

    # 주 선택
    try:
        from sheets.reader import get_available_weekly_starts
        weekly_starts = get_available_weekly_starts()
        if weekly_starts and len(weekly_starts) > 1:
            st.divider()
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

    # run_id 선택 (같은 주에 여러 run 있을 때)
    if 'weekly_run_ids' in dir() and len(weekly_run_ids) > 1:
        st.divider()
        sel_rid = st.selectbox(
            '분석 회차',
            options=weekly_run_ids,
            format_func=lambda x, ids=weekly_run_ids: f'{x}{"  ← 최신" if x == ids[0] else ""}',
            key='sel_weekly_run',
        )
        if sel_rid != selected_run_id:
            st.session_state['report_weekly_run_id'] = sel_rid
            st.rerun()

    st.divider()
    st.markdown(
        f'<div style="font-size:0.72rem;color:#888888;">주 시작: {week_start}</div>',
        unsafe_allow_html=True,
    )


# ── 데이터 없음 처리 ─────────────────────────────────────────────────
if gallery_df.empty:
    st.warning(f'**{week_start}** 주간 분석 결과가 없습니다.')
    st.stop()


gallery_records = gallery_df.to_dict('records')

# week_end 추출
week_end = ''
if not summary_df.empty:
    week_end = str(summary_df.iloc[-1].get('week_end', ''))
elif gallery_records:
    week_end = str(gallery_records[0].get('week_end', ''))


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<div style="font-size:1.4rem;font-weight:800;color:#0A0A0A;margin-bottom:4px;">'
    f'주간 분석 리포트</div>'
    f'<div style="font-size:0.85rem;color:#555555;margin-bottom:20px;">'
    f'<b style="color:#0A0A0A">{week_start}</b> ~ <b style="color:#0A0A0A">{week_end}</b>'
    f'&nbsp;·&nbsp;갤러리 {len(gallery_records)}개</div>',
    unsafe_allow_html=True,
)

# ── KPI ──────────────────────────────────────────────────────────────
total_posts_week = sum(int(r.get('total_posts_week', 0)) for r in gallery_records)
most_active = max(gallery_records, key=lambda r: int(r.get('total_posts_week', 0)), default={})
most_active_name = most_active.get('gallery_name', '-')
most_active_cnt  = int(most_active.get('total_posts_week', 0))

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
        stat_card('가장 활발한 갤러리', most_active_name,
                  sub=f'{most_active_cnt:,}건',
                  tooltip='해당 주 게시글이 가장 많은 갤러리'),
        unsafe_allow_html=True,
    )
with k3:
    avg_posts = int(total_posts_week / len(gallery_records)) if gallery_records else 0
    st.markdown(
        stat_card('갤러리당 평균', f'{avg_posts:,}건',
                  sub='주간 평균',
                  tooltip='전체 갤러리 주간 게시글 평균'),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── AI 종합 요약 ─────────────────────────────────────────────────────
st.markdown(sec_header('주간 종합 요약'), unsafe_allow_html=True)

if not summary_df.empty:
    summary_text = str(summary_df.iloc[-1].get('ai_weekly_summary', ''))
    if summary_text:
        st.markdown(
            cross_card(summary_text.replace('\n', '<br>')),
            unsafe_allow_html=True,
        )
    else:
        st.info('종합 요약이 없습니다.')
else:
    st.info('종합 요약 데이터가 없습니다.')

st.markdown('')

# ── 정규화 추이 차트 ─────────────────────────────────────────────────
st.markdown(sec_header('갤러리별 주간 게시글 추이 (정규화)'), unsafe_allow_html=True)
st.markdown(
    '<div style="font-size:0.75rem;color:#888888;margin-bottom:8px;">'
    '각 갤러리의 최대값=100 기준으로 정규화. 갤러리 간 상대적 흐름을 비교합니다.</div>',
    unsafe_allow_html=True,
)

try:
    from analyzer.weekly_analyzer import normalize_trends
    trend_series = normalize_trends(gallery_records)

    if trend_series:
        legend_html = ' &nbsp; '.join(
            f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'font-size:0.8rem;color:#333333;">'
            f'<span style="width:10px;height:2px;background:{s["color"]};'
            f'display:inline-block;"></span>'
            f'{s["name"][:8]}{"…" if len(s["name"]) > 8 else ""}</span>'
            for s in trend_series
        )
        st.markdown(
            f'<div class="lc" style="padding:16px 20px;">'
            f'<div style="margin-bottom:10px;">{legend_html}</div>'
            + multiline(trend_series, width=900, height=200)
            + '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.caption('추이 데이터가 없습니다.')
except Exception as e:
    st.caption(f'추이 차트 오류: {e}')

st.markdown('')

# ── 갤러리별 상세 ────────────────────────────────────────────────────
st.markdown(sec_header('갤러리별 상세'), unsafe_allow_html=True)

for idx, result in enumerate(gallery_records):
    name       = result.get('gallery_name', '')
    total      = int(result.get('total_posts_week', 0))
    ai_weekly  = str(result.get('ai_gallery_weekly', ''))
    color      = gallery_color(idx)

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

    kw_tags = ' '.join(
        f'<span class="kw-tag">{kw} <b style="color:#555555">{cnt}</b></span>'
        for kw, cnt in kw_list[:5]
    )

    st.markdown(
        f'<div class="lc">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">'
        f'<span style="width:12px;height:12px;border-radius:3px;background:{color};'
        f'flex-shrink:0;display:inline-block;"></span>'
        f'<div style="font-size:1.0rem;font-weight:800;color:#0A0A0A;">{name}</div>'
        f'<div style="font-size:0.78rem;color:#888888;margin-left:auto;">주간 {total:,}건</div>'
        f'</div>'
        f'<div style="margin-bottom:10px;">{kw_tags if kw_tags else "<span style=\'color:#AAAAAA;font-size:0.78rem;\'>키워드 없음</span>"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # AI 주간 갤러리 요약
    if ai_weekly and not ai_weekly.startswith('>'):
        with st.expander(f'{name} — AI 주간 요약'):
            st.markdown(ai_weekly)
    elif ai_weekly:
        st.caption(ai_weekly)

    # TOP5 게시글
    if top5:
        cols = st.columns(1)
        with cols[0]:
            for rank, post in enumerate(top5[:5], 1):
                title    = post.get('제목', '')
                link     = post.get('링크', '')
                comments = int(post.get('댓글수', 0))
                likes    = int(post.get('추천수', 0))
                views    = int(post.get('조회수', 0))
                date_str = str(post.get('날짜', ''))[:10]
                score    = float(post.get('score', 0))

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

    st.markdown('<hr style="border:none;border-top:1px solid #EEEEEE;margin:12px 0;">', unsafe_allow_html=True)
