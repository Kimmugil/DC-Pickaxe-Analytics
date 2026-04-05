"""
DC-Pickaxe Analytics — 종합 대시보드
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title='DC-Pickaxe Analytics',
    page_icon='⛏️',
    layout='wide',
    initial_sidebar_state='expanded',
)

from dashboard.dash_styles import inject_css, stat_card, sec_header, gallery_color, cross_card, tip
from dashboard.svg_charts import multiline, hbar, wrap
inject_css()


# ── Cache ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_dates():
    from sheets.reader import get_available_dates
    return get_available_dates()

@st.cache_data(ttl=60)
def load_run_ids(date: str):
    from sheets.reader import get_run_ids_for_date
    return get_run_ids_for_date(date)

@st.cache_data(ttl=60)
def load_data(date: str, run_id: str):
    from sheets.reader import get_analysis_results, get_cross_gallery_summary
    return get_analysis_results(date, run_id), get_cross_gallery_summary(date, run_id)

@st.cache_data(ttl=600)
def load_trends(gallery_ids: tuple):
    from sheets.reader import get_gallery_trend
    return {gid: get_gallery_trend(gid, days=30) for gid in gallery_ids}


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

    # ── 날짜 선택 ────────────────────────────────────────────────────
    try:
        available_dates = load_dates()
    except Exception:
        available_dates = []

    today_str = datetime.now().strftime('%Y-%m-%d')

    if available_dates:
        selected_date = st.selectbox('📅 분석 날짜', available_dates,
                                     key='sb_date_overview')
    else:
        _d = st.date_input('📅 분석 날짜',
                           value=datetime.now().date() - timedelta(days=1),
                           max_value=datetime.now().date())
        selected_date = _d.strftime('%Y-%m-%d')

    st.session_state['selected_date'] = selected_date

    # ── 회차 선택 (같은 날짜에 여러 run 있을 때) ──────────────────────
    try:
        run_ids = load_run_ids(selected_date)
    except Exception:
        run_ids = []

    if len(run_ids) > 1:
        run_id_labels = {
            rid: f'{rid}  {"← 최신" if i == 0 else ""}'
            for i, rid in enumerate(run_ids)
        }
        selected_run = st.selectbox(
            '🔁 분석 회차',
            options=run_ids,
            format_func=lambda x: run_id_labels.get(x, x),
            key='sb_run_overview',
        )
    else:
        selected_run = run_ids[0] if run_ids else ''

    st.divider()

    # ── 재분석 버튼 ──────────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:0.72rem;color:#475569;margin-bottom:6px;">'
        '오늘 날짜 기준으로 즉시 분석합니다.<br>'
        '기존 회차는 그대로 보존됩니다.</div>',
        unsafe_allow_html=True,
    )

    run_btn = st.button(
        '🔄 지금 분석 실행',
        use_container_width=True,
        type='primary',
        key='btn_run_overview',
    )

    notion_skip = st.checkbox('Notion 발행 건너뜀', value=False, key='chk_notion_overview')

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

    # ── 갤러리 목록 (현재 날짜 기준) ─────────────────────────────────
    st.markdown(
        '<div style="font-size:0.7rem;font-weight:700;color:#475569;'
        'letter-spacing:.06em;margin-bottom:8px;">GALLERY</div>',
        unsafe_allow_html=True,
    )
    try:
        _res, _ = load_data(selected_date, selected_run)
        if not _res.empty:
            for idx, row in _res.iterrows():
                c    = gallery_color(idx)
                name = row.get('gallery_name', '')
                cnt  = int(row.get('new_posts_today', 0))
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:8px;'
                    f'padding:4px 8px;border-radius:7px;">'
                    f'<span style="width:9px;height:9px;border-radius:2px;'
                    f'background:{c};flex-shrink:0;display:inline-block;"></span>'
                    f'<span style="font-size:0.82rem;color:#CBD5E1;flex:1;">{name}</span>'
                    f'<span style="font-size:0.75rem;color:#475569;">{cnt:,}건</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    except Exception:
        pass

    st.divider()
    st.markdown(
        '<div style="font-size:0.7rem;color:#334155;">DC-Pickaxe Analytics</div>',
        unsafe_allow_html=True,
    )


# ── 데이터 로드 ──────────────────────────────────────────────────────
try:
    results_df, cross_df = load_data(selected_date, selected_run)
except Exception as e:
    st.error(f'데이터 로딩 오류: {e}')
    st.stop()

if results_df.empty:
    st.warning(f'**{selected_date}** 의 분석 결과가 아직 없습니다.')
    st.info('사이드바의 **지금 분석 실행** 버튼을 누르거나, GitHub Actions 실행 후 확인해주세요.')
    st.stop()


# ── 페이지 헤더 ──────────────────────────────────────────────────────
run_badge = (
    f'<span style="background:#1E293B;color:#94A3B8;border:1px solid #334155;'
    f'border-radius:5px;font-family:monospace;font-size:0.75rem;padding:2px 7px;">'
    f'회차 {selected_run}</span>' if selected_run else ''
)
st.markdown(
    f'<div style="font-size:1.4rem;font-weight:800;color:#0F172A;margin-bottom:4px;">'
    f'📊 키우기 갤러리 종합 분석</div>'
    f'<div style="font-size:0.82rem;color:#64748B;margin-bottom:20px;display:flex;gap:10px;align-items:center;">'
    f'<span>분석 기준일 <b style="color:#0F172A">{selected_date}</b></span>'
    f'<span>·</span>'
    f'<span>갤러리 <b style="color:#0F172A">{len(results_df)}개</b></span>'
    f'{run_badge}'
    f'</div>',
    unsafe_allow_html=True,
)

# ── KPI 카드 ─────────────────────────────────────────────────────────
total_24h = int(results_df['new_posts_today'].sum()) if 'new_posts_today' in results_df.columns else 0
total_7d  = int(results_df['new_posts_7d'].sum())    if 'new_posts_7d'    in results_df.columns else 0
total_cum = int(results_df['total_posts'].sum())     if 'total_posts'     in results_df.columns else 0

k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        stat_card('24h 전체 신규', f'{total_24h:,}건',
                  sub='분석 기준일 당일 합산', tint='amber',
                  tooltip='분석 기준일 00:00~23:59 게시글 수 (전체 갤러리 합산)'),
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        stat_card('최근 7일 신규', f'{total_7d:,}건',
                  sub='전체 갤러리 합산', tint='green',
                  tooltip='분석 기준일 포함 최근 7일 게시글 수 (전체 갤러리 합산)'),
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        stat_card('누적 게시글', f'{total_cum:,}건',
                  sub='수집된 전체 데이터', tint='blue',
                  tooltip='각 갤러리 시트에 수집된 전체 게시글 수 합산'),
        unsafe_allow_html=True,
    )

# ── 크로스 갤러리 AI 종합 요약 ───────────────────────────────────────
st.markdown('')
st.markdown(sec_header('🌐 오늘의 키우기 장르 종합 동향'), unsafe_allow_html=True)

if not cross_df.empty:
    summary = str(cross_df.iloc[-1].get('ai_cross_summary', ''))
    st.markdown(
        cross_card(summary.replace('\n', '<br>') if summary else '요약 없음'),
        unsafe_allow_html=True,
    )
else:
    st.info(f'{selected_date}의 종합 요약 데이터가 없습니다.')

st.markdown('')

# ── 갤러리별 30일 추이 ────────────────────────────────────────────────
st.markdown(sec_header('📈 갤러리별 게시글 추이 (최근 30일)'), unsafe_allow_html=True)

gallery_ids = tuple(results_df['gallery_id'].tolist()) if 'gallery_id' in results_df.columns else ()

if gallery_ids:
    try:
        trend_map = load_trends(gallery_ids)
        series = []
        for idx, row in results_df.iterrows():
            gid  = row.get('gallery_id', '')
            name = row.get('gallery_name', '')
            data = trend_map.get(gid, [])
            if data:
                series.append({
                    'name':  name,
                    'items': [(d['date'], d['count']) for d in data],
                    'color': gallery_color(idx),
                })

        if series:
            legend_html = ' &nbsp; '.join(
                f'<span style="display:inline-flex;align-items:center;gap:5px;'
                f'font-size:0.8rem;color:#475569;">'
                f'<span style="width:10px;height:10px;border-radius:50%;'
                f'background:{s["color"]};display:inline-block;"></span>'
                f'{s["name"][:7]}{"…" if len(s["name"]) > 7 else ""}</span>'
                for s in series
            )
            st.markdown(
                f'<div class="lc" style="padding:16px 20px;">'
                f'<div style="margin-bottom:10px;">{legend_html}</div>'
                + multiline(series, width=900, height=200)
                + '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption('추이 데이터가 아직 없습니다. 분석이 2일 이상 누적되면 표시됩니다.')
    except Exception as e:
        st.caption(f'추이 차트 로딩 실패: {e}')

st.markdown('')

# ── 갤러리별 현황 카드 ────────────────────────────────────────────────
st.markdown(sec_header('🎮 갤러리별 오늘 현황'), unsafe_allow_html=True)

records = results_df.to_dict('records')
cols    = st.columns(min(3, len(records)))

for i, result in enumerate(records):
    name      = result.get('gallery_name', '')
    new_today = int(result.get('new_posts_today', 0))
    new_7d    = int(result.get('new_posts_7d', 0))
    ai_text   = str(result.get('ai_summary', ''))
    preview   = ''
    for ln in ai_text.split('\n'):
        ln = ln.strip().lstrip('#').lstrip('*').strip()
        if len(ln) > 20:
            preview = ln[:90] + ('…' if len(ln) > 90 else '')
            break
    c   = gallery_color(i)
    col = cols[i % len(cols)]
    with col:
        st.markdown(
            f'<div class="lc" style="border-left:4px solid {c};padding:14px 18px;">'
            f'<div style="font-size:1rem;font-weight:700;color:#0F172A;margin-bottom:8px;">{name}</div>'
            f'<div style="display:flex;gap:14px;font-size:0.8rem;color:#475569;margin-bottom:8px;">'
            f'<span>📝 24h <b style="color:{c}">{new_today:,}</b>건</span>'
            f'<span>📅 7일 <b>{new_7d:,}</b>건</span>'
            f'</div>'
            f'<div style="font-size:0.8rem;color:#64748B;line-height:1.55;">{preview}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown('')

# ── 갤러리별 24h 비교 + 장르 키워드 ─────────────────────────────────
col_bar, col_kw = st.columns(2)

with col_bar:
    st.markdown(sec_header('📊 갤러리별 24h 신규'), unsafe_allow_html=True)
    items = sorted(
        [(r.get('gallery_name', ''), int(r.get('new_posts_today', 0))) for r in records],
        key=lambda x: x[1], reverse=True,
    )
    st.markdown(wrap(hbar(items, label_w=120)), unsafe_allow_html=True)

with col_kw:
    st.markdown(sec_header('🔤 장르 전체 키워드'), unsafe_allow_html=True)
    from collections import Counter
    combined: Counter = Counter()
    for result in records:
        kw_raw = result.get('top_keywords', '[]')
        if isinstance(kw_raw, str):
            try:
                kw_list = json.loads(kw_raw)
            except Exception:
                kw_list = []
        else:
            kw_list = kw_raw or []
        for item in kw_list:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                combined[item[0]] += int(item[1])

    from dashboard.components.keyword_cloud import render_keyword_tags
    render_keyword_tags(combined.most_common(24))
