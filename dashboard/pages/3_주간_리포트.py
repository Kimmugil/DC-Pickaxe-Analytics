"""
DC-Pickaxe Analytics — 주간 분석 리포트 v8
개선사항:
  - 갤러리 색상: 단조 회색 → 8색 비비드 팔레트
  - KPI 구조 교정: '가장 활발한 갤러리' metric 올바른 형식으로
  - 갤러리 정렬: 게시글 수 내림차순 + 순위 표시
  - 주간 추이 멀티라인 차트 추가
  - AI 요약: amber 좌측 보더 블록
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
    st.markdown('**⛏️ DC-Pickaxe**')
    st.divider()
    if st.button('← 캘린더로', use_container_width=True):
        st.switch_page('app.py')
    st.divider()

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

    try:
        weekly_run_ids = get_weekly_run_ids(week_start)
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
    st.caption(f'주: {week_start}')
    rerun_btn = st.button('현재 기준으로 다시 분석', use_container_width=True, key='btn_rerun_weekly')
    if rerun_btn:
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


# ── 데이터 로드 ──────────────────────────────────────────────────────
try:
    gallery_df, summary_df = load_weekly_data(week_start, sel_rid)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()

if gallery_df.empty:
    st.warning(f'**{week_start}** 주간 분석 결과가 없습니다.')
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
    # ── KPI — 구조 교정: 최다 갤러리는 게시글 수가 value ───────────
    total_posts_week = sum(int(r.get('total_posts_week', 0)) for r in gallery_records)
    most_active      = gallery_records[0] if gallery_records else {}
    most_active_name = most_active.get('gallery_name', '-')
    most_active_cnt  = int(most_active.get('total_posts_week', 0))
    avg_posts        = int(total_posts_week / len(gallery_records)) if gallery_records else 0

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric(
            '주간 전체 게시글',
            f'{total_posts_week:,}건',
            help=f'{week_start} ~ {week_end} 전체 갤러리 합산',
        )
    with k2:
        # value = 게시글 수, caption = 갤러리명
        st.metric(
            '주간 최다 게시글',
            f'{most_active_cnt:,}건',
            help=f'가장 활발한 갤러리: {most_active_name}',
        )
        st.caption(f'· {most_active_name}')
    with k3:
        st.metric(
            '갤러리 평균',
            f'{avg_posts:,}건',
            help='주간 게시글 갤러리 평균',
        )

    st.divider()

    # ── 주간 활동 추이 멀티라인 차트 ─────────────────────────────────
    try:
        from analyzer.weekly_analyzer import normalize_trends
        from dashboard.svg_charts import multiline, wrap
        trend_series = normalize_trends(gallery_records)
        if trend_series:
            ml_svg = multiline(trend_series, width=900, height=200)
            st.markdown(
                wrap(ml_svg, '갤러리별 주간 활동 추이 (정규화 · 각 갤러리 최대=100)'),
                unsafe_allow_html=True,
            )

            # 범례 (inline style)
            legend_items = ''.join(
                f'<span style="display:inline-flex;align-items:center;gap:4px;'
                f'margin-right:12px;font-size:0.78rem;color:#475569;">'
                f'<span style="display:inline-block;width:12px;height:3px;'
                f'background:{s["color"]};border-radius:2px;"></span>'
                f'{s["name"]}</span>'
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
    st.caption(f'분석 기간: {week_start} ~ {week_end} · Gemini 2.5 Flash 생성')

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

    # ── 갤러리별 상세 카드 (2열 · 게시글 수 내림차순) ─────────────────
    st.subheader('갤러리별 상세')
    st.caption('게시글 수 내림차순 정렬 · TOP 5 선정: Engagement Score = 추천수×2 + 댓글수×3 + 조회수×0.05')

    pairs = [gallery_records[i:i+2] for i in range(0, len(gallery_records), 2)]

    for pair in pairs:
        cols = st.columns(2)
        for col, result in zip(cols, pair):
            with col:
                name      = result.get('gallery_name', '')
                total     = int(result.get('total_posts_week', 0))
                ai_weekly = str(result.get('ai_gallery_weekly', ''))
                # 정렬 후 인덱스 사용 (고정 색상 부여)
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

                # 갤러리 색상 구분 바 (6px — 충분히 눈에 띔)
                st.markdown(
                    f'<div style="height:6px;background:{color};'
                    f'border-radius:3px;margin-bottom:1px;"></div>',
                    unsafe_allow_html=True,
                )

                with st.container(border=True):
                    # 헤더: 순위 + 갤러리명 + 게시글 수
                    col_name, col_cnt = st.columns([3, 1])
                    with col_name:
                        rank_dot = (
                            f'<span style="display:inline-block;width:18px;height:18px;'
                            f'background:{color};border-radius:50%;'
                            f'text-align:center;line-height:18px;'
                            f'font-size:0.65rem;font-weight:700;color:white;'
                            f'margin-right:5px;">{rank}</span>'
                        )
                        st.markdown(
                            f'{rank_dot}<b style="font-size:0.92rem;">{name}</b>',
                            unsafe_allow_html=True,
                        )
                    with col_cnt:
                        st.metric('주간', f'{total:,}건')

                    # 키워드 태그 (inline style)
                    if kw_list:
                        kw_html = ' '.join(kw_tag(kw, cnt) for kw, cnt in kw_list[:5])
                        st.markdown(kw_html, unsafe_allow_html=True)

                    # AI 주간 요약 — amber 구분 블록
                    if ai_weekly and not ai_weekly.startswith('>'):
                        st.markdown(
                            ai_block_html(ai_weekly, 'AI 주간 요약'),
                            unsafe_allow_html=True,
                        )

                    # TOP5
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
