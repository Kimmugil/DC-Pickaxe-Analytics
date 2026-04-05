"""
Plotly 차트 컴포넌트 모음
- 게시글 수 추이 (라인차트)
- 시간대별 분포 (막대차트)
- 인기글 점수 (가로 막대차트)
"""
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st


def render_daily_trend(result: dict, title: str = "게시글 수 추이 (최근 30일)"):
    """일별 게시글 수 라인 차트를 렌더링합니다."""
    daily_trend = result.get('daily_trend', [])
    if isinstance(daily_trend, str):
        try:
            daily_trend = json.loads(daily_trend)
        except Exception:
            daily_trend = []

    if not daily_trend:
        st.caption("추이 데이터가 없습니다.")
        return

    df = pd.DataFrame(daily_trend)
    if df.empty or 'date' not in df.columns:
        return

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')

    fig = px.line(
        df, x='date', y='count',
        markers=True,
        labels={'date': '날짜', 'count': '게시글 수'},
        title=title,
    )
    fig.update_traces(line_color='#FF4B4B', marker_color='#FF4B4B')
    fig.update_layout(
        height=280,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#F0F2F6'),
        yaxis=dict(showgrid=True, gridcolor='#F0F2F6'),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_hourly_dist(hourly_dist: dict | str, title: str = "시간대별 게시글 분포"):
    """24시간 막대 차트를 렌더링합니다."""
    if isinstance(hourly_dist, str):
        try:
            hourly_dist = json.loads(hourly_dist)
        except Exception:
            hourly_dist = {}

    if not hourly_dist:
        st.caption("시간대 분포 데이터가 없습니다.")
        return

    hours = [str(h) for h in range(24)]
    counts = [int(hourly_dist.get(h, 0)) for h in hours]
    peak = counts.index(max(counts)) if counts else 0
    colors = ['#FF4B4B' if i == peak else '#ADB5BD' for i in range(24)]

    fig = go.Figure(go.Bar(
        x=[f"{h}시" for h in range(24)],
        y=counts,
        marker_color=colors,
        hovertemplate='%{x}: %{y}건<extra></extra>',
    ))
    fig.update_layout(
        title=title,
        height=240,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        yaxis=dict(showgrid=True, gridcolor='#F0F2F6'),
        xaxis=dict(tickfont=dict(size=10)),
    )
    st.plotly_chart(fig, use_container_width=True)


def render_multi_gallery_trend(all_results: list):
    """여러 갤러리의 오늘 신규 게시글 수를 비교하는 가로 막대 차트."""
    if not all_results:
        return

    names  = [r.get('gallery_name', '') for r in all_results]
    counts = [int(r.get('new_posts_today', 0)) for r in all_results]

    df = pd.DataFrame({'gallery': names, 'count': counts}).sort_values('count')

    fig = px.bar(
        df, x='count', y='gallery', orientation='h',
        labels={'count': '오늘 신규 게시글', 'gallery': ''},
        title='갤러리별 오늘 신규 게시글 수',
        color='count',
        color_continuous_scale=['#FECDD3', '#FF4B4B'],
    )
    fig.update_layout(
        height=max(200, len(names) * 40 + 80),
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white',
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
