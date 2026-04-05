"""
SVG 차트 컴포넌트 — plotly 대신 순수 SVG 사용
- 게시글 수 추이 (라인차트)
- 시간대별 분포 (세로 막대)
- 갤러리 비교 (가로 막대)
"""
import json
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dashboard.svg_charts import vbar, hbar, line, wrap


def render_daily_trend(result: dict, title: str = '게시글 수 추이 (최근 30일)'):
    """일별 게시글 수 라인 차트를 렌더링합니다."""
    daily_trend = result.get('daily_trend', [])
    if isinstance(daily_trend, str):
        try:
            daily_trend = json.loads(daily_trend)
        except Exception:
            daily_trend = []

    if not daily_trend:
        st.caption('추이 데이터가 없습니다.')
        return

    items = sorted(
        [(d.get('date', ''), int(d.get('count', 0))) for d in daily_trend],
        key=lambda x: x[0],
    )
    svg = line(items, height=130)
    st.markdown(wrap(svg, title), unsafe_allow_html=True)


def render_hourly_dist(hourly_dist: dict | str, title: str = '시간대별 게시글 분포'):
    """24시간 세로 막대 차트를 렌더링합니다."""
    if isinstance(hourly_dist, str):
        try:
            hourly_dist = json.loads(hourly_dist)
        except Exception:
            hourly_dist = {}

    if not hourly_dist:
        st.caption('시간대 분포 데이터가 없습니다.')
        return

    # 0~23 순서 보장
    ordered = {str(h): int(hourly_dist.get(str(h), 0)) for h in range(24)}
    svg = vbar(ordered, height=155)
    st.markdown(wrap(svg, title), unsafe_allow_html=True)


def render_multi_gallery_trend(all_results: list, title: str = '갤러리별 24h 신규 게시글'):
    """여러 갤러리의 오늘 신규 게시글 수를 가로 막대 차트로 렌더링합니다."""
    if not all_results:
        return

    # 내림차순 정렬 (위에 많은 쪽)
    items = sorted(
        [(r.get('gallery_name', ''), int(r.get('new_posts_today', 0))) for r in all_results],
        key=lambda x: x[1],
        reverse=True,
    )
    height = max(80, len(items) * 28 + 20)
    svg = hbar(items, label_w=120)
    st.markdown(wrap(svg, title), unsafe_allow_html=True)
