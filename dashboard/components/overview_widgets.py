"""
종합 화면 위젯 컴포넌트
- 크로스 갤러리 AI 요약
- 갤러리 카드 그리드
- 장르 전체 키워드 합산
"""
import json
import pandas as pd
import streamlit as st

from dashboard.components.trend_charts import render_multi_gallery_trend
from dashboard.components.keyword_cloud import render_keyword_tags


def render_cross_summary(cross_df: pd.DataFrame, date_str: str):
    """크로스 갤러리 종합 AI 요약을 렌더링합니다."""
    if cross_df.empty:
        st.info(f"{date_str}의 종합 요약 데이터가 없습니다.")
        return

    summary = cross_df.iloc[-1].get('ai_cross_summary', '')
    run_id  = cross_df.iloc[-1].get('run_id', '')

    st.markdown(summary)
    if run_id:
        st.caption(f"분석 회차 ID: `{run_id}`")


def render_gallery_cards(results_df: pd.DataFrame):
    """갤러리별 요약 카드를 그리드로 렌더링합니다."""
    if results_df.empty:
        return

    records = results_df.to_dict('records')
    cols = st.columns(min(3, len(records)))

    for i, result in enumerate(records):
        col = cols[i % len(cols)]
        with col:
            _render_single_card(result)


def _render_single_card(result: dict):
    """갤러리 카드 1개를 렌더링합니다."""
    name       = result.get('gallery_name', '')
    new_today  = int(result.get('new_posts_today', 0))
    new_7d     = int(result.get('new_posts_7d', 0))
    authors    = int(result.get('active_authors', 0))
    ai_summary = str(result.get('ai_summary', ''))

    # 요약의 첫 번째 이슈 항목만 미리보기
    preview = ''
    for line in ai_summary.split('\n'):
        line = line.strip().lstrip('#').lstrip('*').strip()
        if len(line) > 20:
            preview = line[:80] + ('…' if len(line) > 80 else '')
            break

    st.markdown(
        f"""
        <div style="
            padding:16px; border-radius:10px;
            border:1px solid #E9ECEF;
            background:white;
            margin-bottom:12px;
            box-shadow:0 1px 4px rgba(0,0,0,.06);
        ">
            <div style="font-size:1rem; font-weight:700; color:#31333F;">{name}</div>
            <div style="display:flex; gap:16px; margin:8px 0; font-size:0.82rem; color:#495057;">
                <span>📝 오늘 <b style="color:#FF4B4B">{new_today:,}</b>건</span>
                <span>📅 7일 <b>{new_7d:,}</b>건</span>
                <span>👤 <b>{authors:,}</b>명</span>
            </div>
            <div style="font-size:0.83rem; color:#6C757D; line-height:1.5;">{preview}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_genre_keywords(results_df: pd.DataFrame):
    """전체 갤러리의 키워드를 합산해 장르 전체 트렌드 키워드를 표시합니다."""
    from collections import Counter

    combined: Counter = Counter()
    for _, row in results_df.iterrows():
        kw_raw = row.get('top_keywords', '[]')
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

    if not combined:
        st.caption("키워드 데이터가 없습니다.")
        return

    top_keywords = combined.most_common(25)
    render_keyword_tags(top_keywords)
