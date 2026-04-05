"""
키워드 시각화 컴포넌트
- 빈도 기반 태그 클라우드 (HTML 배지)
- 키워드 빈도 막대 차트
"""
import json
import math
import pandas as pd
import plotly.express as px
import streamlit as st


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
        st.caption("키워드 데이터가 없습니다.")
        return

    kw_list = keywords[:max_show]
    if not kw_list:
        return

    max_cnt = max(cnt for _, cnt in kw_list) if kw_list else 1

    tags_html = ""
    for word, cnt in kw_list:
        ratio = cnt / max_cnt
        size  = round(0.75 + ratio * 0.75, 2)   # 0.75rem ~ 1.5rem
        alpha = round(0.4 + ratio * 0.6, 2)       # 0.4 ~ 1.0 투명도
        color = f"rgba(255, 75, 75, {alpha})"
        tags_html += (
            f'<span style="'
            f'display:inline-block;'
            f'margin:3px 4px;'
            f'padding:3px 10px;'
            f'background:{color};'
            f'color:white;'
            f'border-radius:20px;'
            f'font-size:{size}rem;'
            f'font-weight:500;'
            f'">{word} <small style="opacity:.8">({cnt})</small></span>'
        )

    st.markdown(
        f'<div style="line-height:2.2">{tags_html}</div>',
        unsafe_allow_html=True,
    )


def render_keyword_bar(keywords: list | str, top_n: int = 15, title: str = "키워드 빈도"):
    """상위 N개 키워드를 가로 막대 차트로 렌더링합니다."""
    if isinstance(keywords, str):
        try:
            keywords = json.loads(keywords)
        except Exception:
            keywords = []

    if not keywords:
        return

    kw_list = keywords[:top_n]
    df = pd.DataFrame(kw_list, columns=['keyword', 'count']).sort_values('count')

    fig = px.bar(
        df, x='count', y='keyword', orientation='h',
        labels={'count': '등장 횟수', 'keyword': ''},
        title=title,
        color='count',
        color_continuous_scale=['#FECDD3', '#FF4B4B'],
    )
    fig.update_layout(
        height=max(200, len(kw_list) * 28 + 60),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
