"""
DC-Pickaxe Analytics — 주간 분석 리포트 v9
IA 개편:
  - 브레드크럼: 홈 › 리포트 목록 › 주 시작일
  - 이전/다음 주 이동 버튼 (prev/next week nav)
  - 사이드바 '← 캘린더로' 제거 (브레드크럼으로 대체)
탭 구조: [📊 주간 리포트] [🔍 분석 방법론]
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

from dashboard.dash_styles import (
    inject_css, gallery_color, kw_tag, ai_block_html,
    METHODOLOGY_WEEKLY_TEMPLATE,
)
inject_css()


# ── 주 시작일 결정 ───────────────────────────────────────────────────
week_start = st.session_state.get('report_week_start', '')
if not week_start:
    week_start = st.query_params.get('week_start', '')


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_all_weekly_starts() -> list[str]:
    from sheets.reader import get_available_weekly_starts
    return sorted(get_available_weekly_starts())  # ascending


@st.cache_data(ttl=60)
def load_weekly_data(ws: str, run_id: str = None):
    from sheets.reader import get_weekly_gallery_results, get_weekly_summary
    gallery_df = get_weekly_gallery_results(ws, run_id=run_id)
    summary_df = get_weekly_summary(ws)
    return gallery_df, summary_df


# ── Prev / Next 주 계산 ───────────────────────────────────────────────
try:
    all_weeks = load_all_weekly_starts()
    if week_start in all_weeks:
        idx     = all_weeks.index(week_start)
        prev_w  = all_weeks[idx - 1] if idx > 0 else None
        next_w  = all_weeks[idx + 1] if idx < len(all_weeks) - 1 else None
    else:
        prev_w = next_w = None
except Exception:
    prev_w = next_w = None


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('**⛏️ DC-Pickaxe**')
    st.divider()

    try:
        from sheets.reader import get_weekly_run_ids
        weekly_run_ids = get_weekly_run_ids(week_start) if week_start else []
    except Exception:
        weekly_run_ids = []

    selected_run_id = st.session_state.get(
        'report_weekly_run_id',
        weekly_run_ids[0] if weekly_run_ids else None,
    )

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
    if week_start:
        st.caption(f'분석 주: **{week_start}**')
    rerun_btn = st.button('다시 분석', use_container_width=True, key='btn_rerun_weekly')
    if rerun_btn and week_start:
        from dashboard.analysis_runner import run_weekly_now
        with st.spinner(f'{week_start} 재분석 중...'):
            success, output = run_weekly_now(week_start)
        if success:
            st.cache_data.clear()
            st.success('완료!')
            st.rerun()
        else:
            st.error('재분석 실패')
            with st.expander('오류 로그'):
                st.code(output[:3000])


# ── 브레드크럼 ───────────────────────────────────────────────────────
bc1, bc2, bc3, bc4, bc5 = st.columns([0.7, 0.15, 1.2, 0.15, 5])
with bc1:
    st.page_link('app.py', label='🏠 홈')
with bc2:
    st.caption('›')
with bc3:
    st.page_link('pages/1_리포트_목록.py', label='리포트 목록')
with bc4:
    st.caption('›')
with bc5:
    st.caption(f'**{week_start}** 주간 분석 리포트' if week_start else '주간 분석 리포트')


# ── 날짜 미지정 처리 ─────────────────────────────────────────────────
if not week_start:
    st.warning('주 시작일이 지정되지 않았습니다.')
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button('← 홈으로', use_container_width=True):
            st.switch_page('app.py')
    with col_b:
        if st.button('리포트 목록', use_container_width=True):
            st.switch_page('pages/1_리포트_목록.py')
    st.stop()


# ── 이전/다음 주 내비게이션 ──────────────────────────────────────────
nav_p, nav_c, nav_n = st.columns([2, 4, 2])
with nav_p:
    if prev_w:
        if st.button(f'← {prev_w}', use_container_width=True, key='nav_prev_week'):
            st.session_state['report_week_start'] = prev_w
            st.session_state.pop('report_weekly_run_id', None)
            st.rerun()
with nav_c:
    st.markdown(
        f'<div style="text-align:center;font-size:0.82rem;color:#94A3B8;padding-top:6px;">'
        f'{week_start} 주</div>',
        unsafe_allow_html=True,
    )
with nav_n:
    if next_w:
        if st.button(f'{next_w} →', use_container_width=True, key='nav_next_week'):
            st.session_state['report_week_start'] = next_w
            st.session_state.pop('report_weekly_run_id', None)
            st.rerun()

st.markdown('<div style="height:2px;"></div>', unsafe_allow_html=True)


# ── 데이터 로드 ──────────────────────────────────────────────────────
try:
    gallery_df, summary_df = load_weekly_data(week_start, sel_rid)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()

if gallery_df.empty:
    st.warning(f'**{week_start}** 주간 분석 결과가 없습니다.')
    if st.button('← 리포트 목록으로'):
        st.switch_page('pages/1_리포트_목록.py')
    st.stop()

# 게시글 수 내림차순 정렬
gallery_records = sorted(
    gallery_df.to_dict('records'),
    key=lambda r: int(r.get('total_posts_week', 0)),
    reverse=True,
)
week_end = ''
if not summary_df.empty:
    week_end = str(summary_df.iloc[-1].get('week_end', ''))
elif gallery_records:
    week_end = str(gallery_records[0].get('week_end', ''))


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.title('주간 분석 리포트')
st.caption(
    f'분석 기간: **{week_start} ~ {week_end}** · '
    f'갤러리 **{len(gallery_records)}개**'
    + (f' · 회차: {sel_rid}' if sel_rid else '')
)

# ── 탭 구조 ──────────────────────────────────────────────────────────
tab_report, tab_method = st.tabs(['📊 주간 리포트', '🔍 분석 방법론'])

with tab_report:
    # ── KPI ───────────────────────────────────────────────────────────
    total_posts_week = sum(int(r.get('total_posts_week', 0)) for r in gallery_records)
    most_active      = gallery_records[0] if gallery_records else {}
    most_active_name = most_active.get('gallery_name', '-')
    most_active_cnt  = int(most_active.get('total_posts_week', 0))
    avg_posts        = int(total_posts_week / len(gallery_records)) if gallery_records else 0

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric('주간 전체 게시글', f'{total_posts_week:,}건',
                  help=f'{week_start} ~ {week_end} 전체 합산')
    with k2:
        st.metric('주간 최다 게시글', f'{most_active_cnt:,}건',
                  help=f'가장 활발: {most_active_name}')
        st.caption(f'· {most_active_name}')
    with k3:
        st.metric('갤러리 평균', f'{avg_posts:,}건',
                  help='주간 게시글 갤러리 평균')

    st.divider()

    # ── 주간 활동 추이 차트 ────────────────────────────────────────────
    try:
        from analyzer.weekly_analyzer import normalize_trends
        from dashboard.svg_charts import multiline, wrap
        trend_series = normalize_trends(gallery_records)
        if trend_series:
            ml_svg = multiline(trend_series, width=900, height=200)
            st.markdown(wrap(ml_svg, '갤러리별 주간 활동 추이 (정규화 · 최대=100)'), unsafe_allow_html=True)
            legend_items = ''.join(
                f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'margin-right:12px;font-size:0.78rem;color:#475569;">'
                f'<span style="display:inline-block;width:12px;height:3px;'
                f'background:{s["color"]};border-radius:2px;"></span>{s["name"]}</span>'
                for s in trend_series
            )
            st.markdown(
                f'<div style="margin-top:4px;margin-bottom:8px;">{legend_items}</div>',
                unsafe_allow_html=True,
            )
    except Exception:
        pass

    st.divider()

    # ── AI 종합 요약 ──────────────────────────────────────────────────
    st.subheader('AI 주간 종합 요약')
    st.caption(f'{week_start} ~ {week_end} · Gemini 2.5 Flash 생성')

    if not summary_df.empty:
        latest_row   = summary_df.iloc[-1]
        summary_text = str(latest_row.get('ai_weekly_summary', ''))
        if summary_text and not summary_text.startswith('>'):
            with st.container(border=True):
                st.markdown(summary_text)
        else:
            st.info('종합 요약이 없습니다.')
    else:
        st.info('종합 요약 데이터가 없습니다.')

    st.divider()

    # ── 갤러리별 카드 (2열 · 게시글 수 내림차순) ─────────────────────
    st.subheader('갤러리별 상세')
    st.caption('게시글 수 내림차순 · TOP 5 기준: Engagement Score = 추천수×2 + 댓글수×3 + 조회수×0.05')

    pairs = [gallery_records[i:i+2] for i in range(0, len(gallery_records), 2)]

    for pair in pairs:
        cols = st.columns(2)
        for col, result in zip(cols, pair):
            with col:
                name      = result.get('gallery_name', '')
                total     = int(result.get('total_posts_week', 0))
                ai_weekly = str(result.get('ai_gallery_weekly', ''))
                idx       = gallery_records.index(result)
                color     = gallery_color(idx)
                rank      = idx + 1

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

                # 6px 갤러리 컬러 바
                st.markdown(
                    f'<div style="height:6px;background:{color};border-radius:3px;margin-bottom:1px;"></div>',
                    unsafe_allow_html=True,
                )

                with st.container(border=True):
                    col_name, col_cnt = st.columns([3, 1])
                    with col_name:
                        rank_dot = (
                            f'<span style="display:inline-block;width:18px;height:18px;'
                            f'background:{color};border-radius:50%;text-align:center;'
                            f'line-height:18px;font-size:0.65rem;font-weight:700;'
                            f'color:white;margin-right:5px;">{rank}</span>'
                        )
                        st.markdown(
                            f'{rank_dot}<b style="font-size:0.92rem;">{name}</b>',
                            unsafe_allow_html=True,
                        )
                    with col_cnt:
                        st.metric('주간', f'{total:,}건')

                    if kw_list:
                        kw_html = ' '.join(kw_tag(kw, cnt) for kw, cnt in kw_list[:5])
                        st.markdown(kw_html, unsafe_allow_html=True)

                    if ai_weekly and not ai_weekly.startswith('>'):
                        st.markdown(ai_block_html(ai_weekly, 'AI 주간 요약'), unsafe_allow_html=True)

                    if top5:
                        with st.expander('TOP 5 인기 게시글'):
                            for rank_p, post in enumerate(top5[:5], 1):
                                title    = post.get('제목', '')
                                link     = post.get('링크', '')
                                comments = int(post.get('댓글수', 0))
                                likes    = int(post.get('추천수', 0))
                                views    = int(post.get('조회수', 0))
                                score    = post.get('score', '')
                                date_str = str(post.get('날짜', ''))[:10]
                                t_disp   = f'[{title}]({link})' if link else title
                                score_str = f' · score {score}' if score else ''
                                st.markdown(
                                    f'**{rank_p}.** {t_disp}  \n'
                                    f'💬 {comments} &nbsp;👍 {likes} &nbsp;👁 {views:,}'
                                    f' &nbsp;·&nbsp; {date_str}{score_str}'
                                )


with tab_method:
    st.markdown(METHODOLOGY_WEEKLY_TEMPLATE.format(
        week_start=week_start,
        week_end=week_end,
    ))
