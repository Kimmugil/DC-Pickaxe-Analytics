"""
키워드 시각화 컴포넌트 — plotly 대신 순수 SVG/HTML 사용
- 빈도 기반 태그 클라우드 (HTML 배지)
- 키워드 빈도 가로 막대 차트 (SVG)
"""
import json
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.svg_charts import hbar, wrap


def render_keyword_tags(keywords: list | str, max_show: int = 20):
    """
    HTML 배지 형태의 키워드 태그 클라우드를 렌더링합니다.
    빈도에 비례해 폰트 크기가 커집니다.
    """
    if isinstance(keywords, str):
        try:
            keywords = json.loads(keywords)
        except Exception:
            keywords = []

    if not keywords:
        st.caption('키워드 데이터가 없습니다.')
        return

    kw_list = keywords[:max_show]
    if not kw_list:
        return

    max_cnt = max(cnt for _, cnt in kw_list) if kw_list else 1

    tags_html = ''
    for word, cnt in kw_list:
        ratio  = cnt / max_cnt
        size   = round(0.75 + ratio * 0.75, 2)   # 0.75 ~ 1.5rem
        alpha  = round(0.35 + ratio * 0.65, 2)    # 0.35 ~ 1.0
        color  = f'rgba(255, 176, 32, {alpha})'   # amber
        tags_html += (
            f'<span class="kw-tag" style="background:{color};font-size:{size}rem;">'
            f'{word} <small style="opacity:.75">({cnt})</small></span>'
        )

    st.markdown(
        f'<div style="line-height:2.4">{tags_html}</div>',
        unsafe_allow_html=True,
    )


def render_keyword_bar(keywords: list | str, top_n: int = 15, title: str = '키워드 빈도'):
    """상위 N개 키워드를 가로 막대 차트(SVG)로 렌더링합니다."""
    if isinstance(keywords, str):
        try:
            keywords = json.loads(keywords)
        except Exception:
            keywords = []

    if not keywords:
        return

    items = [(kw, cnt) for kw, cnt in keywords[:top_n]]
    svg   = hbar(items, label_w=100)
    st.markdown(wrap(svg, title), unsafe_allow_html=True)
