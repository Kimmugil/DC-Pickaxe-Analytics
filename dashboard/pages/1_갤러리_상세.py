"""
DC-Pickaxe Analytics — 갤러리별 상세 리포트
이미지 2 레이아웃: 헤더 카드 → 4-stat → [TOP3 | 막대차트] → 누적추이 → AI요약 → 신호
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from datetime import date, timedelta
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='갤러리 상세 | DC-Pickaxe Analytics',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, stat_card, sec_header, hero_card, gallery_color, tip
from dashboard.svg_charts import vbar, hbar, line, wrap
inject_css()


# ── Cache ────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def load_results(d: str):
    from sheets.reader import get_analysis_results
    return get_analysis_results(d)

@st.cache_data(ttl=600)
def load_trend(gallery_id: str):
    from sheets.reader import get_gallery_trend
    return get_gallery_trend(gallery_id, days=30)


# ── 사이드바 ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="font-size:1.15rem;font-weight:800;color:#F1F5F9;'
        'letter-spacing:-.3px;margin-bottom:2px;">⛏️ DC-Pickaxe</div>'
        '<div style="font-size:0.73rem;color:#64748B;margin-bottom:16px;">'
        '키우기 갤러리 분석 대시보드</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    @st.cache_data(ttl=300)
    def _load_dates():
        from sheets.reader import get_available_dates
        return get_available_dates()

    try:
        available_dates = _load_dates()
    except Exception:
        available_dates = []

    if available_dates:
        default     = st.session_state.get('selected_date', available_dates[0])
        default_idx = available_dates.index(default) if default in available_dates else 0
        date_str    = st.selectbox('📅 날짜', available_dates, index=default_idx)
    else:
        _d       = st.date_input('📅 날짜', value=date.today() - timedelta(days=1),
                                  max_value=date.today())
        date_str = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = date_str
    st.divider()

    try:
        results_df = load_results(date_str)
    except Exception as e:
        st.error(f'데이터 로딩 오류: {e}')
        st.stop()

    if results_df.empty:
        st.warning(f'{date_str}의 데이터가 없습니다.')
        st.stop()

    # Gallery nav list
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:700;color:#475569;'
        'letter-spacing:.06em;margin-bottom:8px;">GALLERY</div>',
        unsafe_allow_html=True,
    )
    gallery_names = results_df['gallery_name'].tolist()
    selected_gallery = st.radio('갤러리', gallery_names, label_visibility='collapsed')

    st.divider()
    st.markdown(
        '<div style="font-size:0.7rem;color:#334155;">DC-Pickaxe Analytics</div>',
        unsafe_allow_html=True,
    )


# ── 선택 갤러리 데이터 ────────────────────────────────────────────────
row = results_df[results_df['gallery_name'] == selected_gallery]
if row.empty:
    st.warning('선택한 갤러리의 데이터를 찾을 수 없습니다.')
    st.stop()

result       = row.iloc[0].to_dict()
gallery_idx  = gallery_names.index(selected_gallery)
g_color      = gallery_color(gallery_idx)

run_id       = str(result.get('run_id', ''))
gallery_id   = str(result.get('gallery_id', ''))
new_today    = int(result.get('new_posts_today', 0))
new_7d       = int(result.get('new_posts_7d', 0))
total        = int(result.get('total_posts', 0))
ai_summary   = str(result.get('ai_summary', ''))
top5_raw     = result.get('top5_posts', '[]')
keywords_raw = result.get('top_keywords', '[]')
hourly_raw   = result.get('hourly_dist', '{}')
signals_raw  = result.get('game_signals', '{}')


# ── 갤러리 헤더 카드 ─────────────────────────────────────────────────
# 일평균 계산
daily_avg = round(new_7d / 7, 1) if new_7d else 0

st.markdown(
    f'<div style="background:white;border:1px solid #E2E8F0;border-radius:14px;'
    f'padding:18px 24px 16px;margin-bottom:14px;border-left:5px solid {g_color};'
    f'box-shadow:0 1px 4px rgba(15,23,42,.06);">'
    f'<div style="font-size:1.4rem;font-weight:800;color:#0F172A;">{selected_gallery}</div>'
    f'<div style="font-size:0.8rem;color:#64748B;margin-top:5px;display:flex;align-items:center;gap:10px;">'
    f'<span>ID: <code style="background:#F1F5F9;padding:1px 5px;border-radius:4px;">{gallery_id}</code></span>'
    f'<span style="background:#FFFBEB;color:#92400E;border:1px solid #FDE68A;border-radius:6px;'
    f'font-size:0.75rem;font-weight:700;padding:2px 8px;">분석일 {date_str}</span>'
    f'<span style="background:#F0FDF4;color:#166534;border:1px solid #BBF7D0;border-radius:6px;'
    f'font-size:0.75rem;font-weight:700;padding:2px 8px;">'
    f'회차 {run_id}</span>'
    f'</div></div>',
    unsafe_allow_html=True,
)

# ── 4-stat 행 ────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        stat_card('24h 신규 게시글', f'{new_today:,}건', tint='amber',
                  tooltip='분석 기준일(어제) 00:00~23:59 게시글 수.\n이것이 AI 분석의 핵심 대상입니다.'),
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

# ── [인기글 TOP3] + [일별 막대차트] ─────────────────────────────────
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
        rank_colors = [g_color, '#94A3B8', '#94A3B8', '#94A3B8', '#94A3B8']
        for i, post in enumerate(top5[:5], 1):
            title    = str(post.get('제목', '(제목 없음)'))
            link     = str(post.get('링크', ''))
            likes    = int(post.get('추천수', 0))
            comments = int(post.get('댓글수', 0))
            p_date   = str(post.get('날짜', ''))[:10]
            rc       = rank_colors[i - 1] if i <= len(rank_colors) else '#94A3B8'

            title_html = (
                f'<a href="{link}" target="_blank" '
                f'style="color:#0F172A;text-decoration:none;">{title}</a>'
                if link else title
            )
            st.markdown(
                f'<div class="top-post" style="border-left-color:{rc};">'
                f'<div class="top-post-rank" style="color:{rc};">{i}</div>'
                f'<div>'
                f'<div class="top-post-title">{title_html}</div>'
                f'<div class="top-post-meta">{p_date} &nbsp;·&nbsp; '
                f'👍 {likes:,} &nbsp; 💬 {comments:,}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption('인기글 데이터가 없습니다.')

with col_bar:
    st.markdown(sec_header('📊 시간대별 활성도'), unsafe_allow_html=True)
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
            wrap(vbar(ordered, height=155, color=g_color), '24h 시간대 분포'),
            unsafe_allow_html=True,
        )
    else:
        st.caption('시간대 데이터가 없습니다.')

st.markdown('')

# ── 30일 일별 추이 (전폭) ─────────────────────────────────────────────
st.markdown(sec_header('📈 게시글 수 추이 (최근 30일)'), unsafe_allow_html=True)

if gallery_id:
    try:
        trend_data = load_trend(gallery_id)
        if trend_data:
            items = [(d['date'], d['count']) for d in trend_data]
            st.markdown(
                wrap(line(items, height=140, color=g_color), '일별 24h 신규 게시글'),
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
else:
    st.caption('갤러리 ID가 없어 추이를 불러올 수 없습니다.')

st.markdown('')

# ── AI 분석 요약 ─────────────────────────────────────────────────────
st.markdown(sec_header('🤖 AI 분석 요약'), unsafe_allow_html=True)

st.markdown(
    f'<div class="lc" style="border-left:4px solid {g_color};line-height:1.75;">'
    f'{ai_summary if ai_summary else "<span style=\\"color:#94A3B8\\">요약 데이터가 없습니다.</span>"}'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown('')

# ── 키워드 + 게임 신호 ────────────────────────────────────────────────
col_kw, col_sig = st.columns(2)

with col_kw:
    st.markdown(sec_header('🔤 키워드 트렌드'), unsafe_allow_html=True)
    from dashboard.components.keyword_cloud import render_keyword_tags, render_keyword_bar
    render_keyword_tags(keywords_raw)
    with st.expander('막대 차트로 보기'):
        render_keyword_bar(keywords_raw)

with col_sig:
    st.markdown(
        sec_header('🎯 게임 특화 신호')
        + ' '
        + tip('각 신호의 % = 관련 키워드가 포함된 게시글 비율.\n5% 이상 주의, 10% 이상 경보.'),
        unsafe_allow_html=True,
    )

    if isinstance(signals_raw, str):
        try:
            signals = json.loads(signals_raw)
        except Exception:
            signals = {}
    else:
        signals = signals_raw or {}

    if signals:
        sorted_sigs = sorted(
            [(k, v) for k, v in signals.items() if isinstance(v, dict)],
            key=lambda x: x[1].get('ratio', 0), reverse=True,
        )
        for _, sig in sorted_sigs:
            label    = sig.get('label', '')
            ratio    = sig.get('ratio', 0)
            pc       = sig.get('post_count', '-')
            pct      = min(int(ratio), 100)
            bar_c    = '#EF4444' if ratio >= 10 else ('#F97316' if ratio >= 5 else '#94A3B8')
            st.markdown(
                f'<div class="sig-card">'
                f'<div class="sig-label">{label}</div>'
                f'<div class="sig-bar-bg"><div class="sig-bar-fill" '
                f'style="width:{pct}%;background:{bar_c};"></div></div>'
                f'<div class="sig-meta">관련 게시글 {pc}건 &nbsp;·&nbsp; 비율 <b>{ratio}%</b></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption('게임 특화 지표 데이터가 없습니다.')

st.markdown('')

# ── 분석 회차 ────────────────────────────────────────────────────────
with st.expander(f'🔍 분석 회차 정보 (run_id: {run_id})'):
    st.markdown(f"""
**분석 회차 ID**: `{run_id}`

- **Google Sheets** → `분석대상게시글` 탭 → `run_id = {run_id}` 로 필터
- **재분석 명령어**: `python run_analysis.py --rerun {run_id}`
    """)
