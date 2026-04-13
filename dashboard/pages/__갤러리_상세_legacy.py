"""
DC-Pickaxe Analytics — 갤러리별 상세 리포트
헤더 카드 → 4-stat → [TOP5 | 시간대] → 추이 → AI요약 → 키워드+신호
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from datetime import datetime, timedelta, date as date_type
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='갤러리 상세 | DC-Pickaxe Analytics',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, stat_card, sec_header, gallery_color, tip
from dashboard.svg_charts import vbar, hbar, line, wrap
inject_css()


# ── Cache ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _load_dates():
    from sheets.reader import get_available_dates
    return get_available_dates()

@st.cache_data(ttl=60)
def _load_run_ids(date: str):
    from sheets.reader import get_run_ids_for_date
    return get_run_ids_for_date(date)

@st.cache_data(ttl=60)
def _load_results(date: str, run_id: str):
    from sheets.reader import get_analysis_results
    return get_analysis_results(date, run_id)

@st.cache_data(ttl=600)
def _load_trend(gallery_id: str):
    from sheets.reader import get_gallery_trend
    return get_gallery_trend(gallery_id, days=30)


# ── 사이드바 ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F1F5F9;'
        'letter-spacing:-.3px;margin-bottom:2px;">⛏️ DC-Pickaxe</div>'
        '<div style="font-size:0.73rem;color:#64748B;margin-bottom:16px;">'
        '키우기 갤러리 분석 대시보드</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    # ── 날짜 선택 ──────────────────────────────────────────────────────
    try:
        available_dates = _load_dates()
    except Exception:
        available_dates = []

    today_str = datetime.now().strftime('%Y-%m-%d')

    if available_dates:
        default     = st.session_state.get('selected_date', available_dates[0])
        default_idx = available_dates.index(default) if default in available_dates else 0
        date_str    = st.selectbox('📅 날짜', available_dates, index=default_idx, key='sb_date_detail')
    else:
        _d       = st.date_input('📅 날짜',
                                  value=datetime.now().date() - timedelta(days=1),
                                  max_value=datetime.now().date())
        date_str = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = date_str

    # ── 회차 선택 ──────────────────────────────────────────────────────
    try:
        run_ids = _load_run_ids(date_str)
    except Exception:
        run_ids = []

    if len(run_ids) > 1:
        run_id_labels = {
            rid: f'{rid}  {"← 최신" if i == 0 else f"({i+1}번째)"}'
            for i, rid in enumerate(run_ids)
        }
        selected_run = st.selectbox(
            '🔁 분석 회차',
            options=run_ids,
            format_func=lambda x: run_id_labels.get(x, x),
            key='sb_run_detail',
        )
        st.caption(f'{len(run_ids)}개 회차 존재 · 최신이 기본값')
    else:
        selected_run = run_ids[0] if run_ids else ''

    st.divider()

    # ── 재분석 버튼 ────────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;margin-bottom:6px;">'
        '오늘 날짜 기준으로 즉시 분석합니다.<br>'
        '기존 회차는 그대로 보존됩니다.</div>',
        unsafe_allow_html=True,
    )
    run_btn     = st.button('🔄 지금 분석 실행', use_container_width=True,
                             type='primary', key='btn_run_detail')
    notion_skip = st.checkbox('Notion 발행 건너뜀', value=False, key='chk_notion_detail')

    if run_btn:
        from dashboard.analysis_runner import run_analysis_now
        with st.spinner(f'분석 중... ({today_str} 기준)\n약 2~5분 소요됩니다.'):
            success, output = run_analysis_now(today_str, skip_notion=notion_skip)
        if success:
            st.cache_data.clear()
            st.session_state['selected_date'] = today_str
            st.success('✅ 분석 완료!')
            st.rerun()
        else:
            st.error('❌ 분석 실패')
            with st.expander('오류 로그'):
                st.code(output[:3000])

    st.divider()

    # ── 갤러리 선택 ────────────────────────────────────────────────────
    try:
        results_df = _load_results(date_str, selected_run)
    except Exception as e:
        st.error(f'데이터 로딩 오류: {e}')
        st.stop()

    if results_df.empty:
        st.warning(f'{date_str}의 데이터가 없습니다.')
        st.stop()

    gallery_names    = results_df['gallery_name'].tolist()
    selected_gallery = st.radio('🎮 갤러리', gallery_names, label_visibility='collapsed',
                                 key='radio_gallery_detail')

    st.divider()
    st.markdown(
        '<div style="font-size:0.7rem;color:#334155;">DC-Pickaxe Analytics</div>',
        unsafe_allow_html=True,
    )


# ── 선택 갤러리 데이터 ─────────────────────────────────────────────────
row = results_df[results_df['gallery_name'] == selected_gallery]
if row.empty:
    st.warning('선택한 갤러리의 데이터를 찾을 수 없습니다.')
    st.stop()

result      = row.iloc[0].to_dict()
gallery_idx = gallery_names.index(selected_gallery)
g_color     = gallery_color(gallery_idx)

run_id      = str(result.get('run_id', ''))
gallery_id  = str(result.get('gallery_id', ''))
new_today   = int(result.get('new_posts_today', 0))
new_7d      = int(result.get('new_posts_7d', 0))
total       = int(result.get('total_posts', 0))
ai_summary  = str(result.get('ai_summary', ''))
top5_raw    = result.get('top5_posts', '[]')
keywords_raw = result.get('top_keywords', '[]')
hourly_raw  = result.get('hourly_dist', '{}')
signals_raw = result.get('game_signals', '{}')
daily_avg   = round(new_7d / 7, 1) if new_7d else 0


# ── 갤러리 헤더 카드 ──────────────────────────────────────────────────
st.markdown(
    f'<div style="background:white;border:1px solid #E2E8F0;border-radius:14px;'
    f'padding:18px 24px 16px;margin-bottom:14px;border-left:5px solid {g_color};'
    f'box-shadow:0 1px 4px rgba(15,23,42,.06);">'
    f'<div style="font-size:1.4rem;font-weight:800;color:#0F172A;">{selected_gallery}</div>'
    f'<div style="font-size:0.8rem;color:#64748B;margin-top:6px;display:flex;'
    f'align-items:center;gap:10px;flex-wrap:wrap;">'
    f'<span>ID: <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;">{gallery_id}</code></span>'
    f'<span style="background:#FFFBEB;color:#92400E;border:1px solid #FDE68A;'
    f'border-radius:6px;font-size:0.75rem;font-weight:700;padding:2px 8px;">'
    f'분석일 {date_str}</span>'
    f'<span style="background:#F1F5F9;color:#475569;border:1px solid #E2E8F0;'
    f'border-radius:6px;font-family:monospace;font-size:0.74rem;padding:2px 8px;">'
    f'회차 {run_id}</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)

# ── 4-stat 행 ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        stat_card('24h 신규 게시글', f'{new_today:,}건', tint='amber',
                  tooltip='분석 기준일 00:00~23:59 게시글 수.\nAI 분석의 핵심 대상입니다.'),
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        stat_card('최근 7일 신규', f'{new_7d:,}건', tint='green',
                  tooltip='분석 기준일 포함 최근 7일 게시글 수.\n5건 미만이면 AI 요약이 생성되지 않습니다.'),
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        stat_card('누적 게시글', f'{total:,}건', tint='blue',
                  tooltip='이 갤러리 시트에 수집된 전체 게시글 수입니다.'),
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        stat_card('7일 일평균', f'{daily_avg:,}건/일', tint='purple',
                  tooltip='최근 7일 신규 ÷ 7로 계산한 일평균 게시글 수입니다.'),
        unsafe_allow_html=True,
    )

st.markdown('')

# ── [인기글 TOP5] + [시간대 막대] ────────────────────────────────────
col_top, col_bar = st.columns([1, 1])

with col_top:
    st.markdown(sec_header('🔥 인기글 TOP 5'), unsafe_allow_html=True)
    if isinstance(top5_raw, str):
        try:
            top5 = json.loads(top5_raw)
        except Exception:
            top5 = []
    else:
        top5 = top5_raw or []

    if top5:
        for i, post in enumerate(top5[:5], 1):
            title    = str(post.get('제목', '(제목 없음)'))
            link     = str(post.get('링크', ''))
            likes    = int(post.get('추천수', 0))
            comments = int(post.get('댓글수', 0))
            p_date   = str(post.get('날짜', ''))[:10]
            rank_c   = g_color if i == 1 else '#94A3B8'
            title_html = (
                f'<a href="{link}" target="_blank" '
                f'style="color:#0F172A;text-decoration:none;">{title}</a>'
                if link else title
            )
            st.markdown(
                f'<div class="top-post" style="border-left-color:{rank_c};">'
                f'<div class="top-post-rank" style="color:{rank_c};">{i}</div>'
                f'<div>'
                f'<div class="top-post-title">{title_html}</div>'
                f'<div class="top-post-meta">{p_date} &nbsp;·&nbsp; '
                f'👍 {likes:,} 💬 {comments:,}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption('인기글 데이터가 없습니다.')

with col_bar:
    st.markdown(sec_header('🕐 시간대별 활성도'), unsafe_allow_html=True)
    if isinstance(hourly_raw, str):
        try:
            hourly = json.loads(hourly_raw)
        except Exception:
            hourly = {}
    else:
        hourly = hourly_raw or {}

    if hourly:
        ordered = {str(h): int(hourly.get(str(h), 0)) for h in range(24)}
        st.markdown(
            wrap(vbar(ordered, height=160, color=g_color), '24h 시간대 분포'),
            unsafe_allow_html=True,
        )
    else:
        st.caption('시간대 데이터가 없습니다.')

st.markdown('')

# ── 30일 일별 추이 ────────────────────────────────────────────────────
st.markdown(sec_header('📈 게시글 수 추이 (최근 30일)'), unsafe_allow_html=True)

if gallery_id:
    try:
        trend_data = _load_trend(gallery_id)
        if trend_data:
            items = [(d['date'], d['count']) for d in trend_data]
            st.markdown(
                wrap(line(items, height=145, color=g_color), '일별 24h 신규 게시글'),
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="lc" style="text-align:center;padding:28px;color:#94A3B8;">'
                '분석이 누적되면 추이 차트가 표시됩니다.</div>',
                unsafe_allow_html=True,
            )
    except Exception as e:
        st.caption(f'추이 데이터 로딩 실패: {e}')

st.markdown('')

# ── AI 분석 요약 ──────────────────────────────────────────────────────
st.markdown(sec_header('🤖 AI 분석 요약'), unsafe_allow_html=True)

st.markdown(
    f'<div class="lc" style="border-left:4px solid {g_color};line-height:1.8;">'
    + (ai_summary if ai_summary
       else '<span style="color:#94A3B8">요약 데이터가 없습니다.</span>')
    + '</div>',
    unsafe_allow_html=True,
)

st.markdown('')

# ── 키워드 + 게임 신호 ─────────────────────────────────────────────────
col_kw, col_sig = st.columns(2)

with col_kw:
    st.markdown(sec_header('🔤 키워드 트렌드'), unsafe_allow_html=True)
    from dashboard.components.keyword_cloud import render_keyword_tags, render_keyword_bar
    render_keyword_tags(keywords_raw)
    with st.expander('막대 차트로 보기'):
        render_keyword_bar(keywords_raw)

with col_sig:
    st.markdown(
        sec_header('🎯 게임 특화 신호') + ' '
        + tip('관련 키워드가 포함된 게시글 비율(%).\n5% 이상 주의 / 10% 이상 경보'),
        unsafe_allow_html=True,
    )

    signals = {}
    if isinstance(signals_raw, str):
        try:
            signals = json.loads(signals_raw)
        except Exception:
            pass
    else:
        signals = signals_raw or {}

    if signals:
        sorted_sigs = sorted(
            [(k, v) for k, v in signals.items() if isinstance(v, dict)],
            key=lambda x: x[1].get('ratio', 0), reverse=True,
        )
        for _, sig in sorted_sigs:
            label  = sig.get('label', '')
            ratio  = sig.get('ratio', 0)
            pc     = sig.get('post_count', '-')
            pct    = min(int(ratio), 100)
            bar_c  = '#EF4444' if ratio >= 10 else ('#F97316' if ratio >= 5 else '#94A3B8')
            st.markdown(
                f'<div class="sig-card">'
                f'<div class="sig-label">{label}</div>'
                f'<div class="sig-bar-bg"><div class="sig-bar-fill" '
                f'style="width:{pct}%;background:{bar_c};"></div></div>'
                f'<div class="sig-meta">관련 게시글 {pc}건 · 비율 <b>{ratio}%</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption('게임 특화 지표 데이터가 없습니다.')

st.markdown('')

# ── 분석 회차 정보 ────────────────────────────────────────────────────
with st.expander(f'🔍 분석 회차 정보 (run_id: {run_id})'):
    st.markdown(f"""
**분석 회차 ID**: `{run_id}`

- **Google Sheets** → `분석대상게시글` 탭 → `run_id = {run_id}` 로 필터
- **재분석 명령어**: `python run_analysis.py --rerun {run_id}`
- **동일 회차 사용 이유**: 이 run_id로 분석에 사용된 게시글 원본을 그대로 복원할 수 있습니다.
    """)
