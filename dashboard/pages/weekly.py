"""
DC-Pickaxe Analytics — 주간 리포트 상세
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="주간 리포트 — DC-Pickaxe",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.style import (
    inject_css, render_sidebar_nav,
    gallery_color, label_html, kw_tag_html, ai_block_html,
    post_row_html, daily_count_bar_html,
    C_TITLE, C_HEADING, C_BODY, C_MUTED, C_LABEL, C_BORDER, C_ACCENT,
)
inject_css()
render_sidebar_nav()


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_week_list() -> list[str]:
    from sheets.reader import get_weekly_gallery_list
    return get_weekly_gallery_list()


@st.cache_data(ttl=120)
def load_weekly(week_start: str):
    from sheets.reader import get_weekly_galleries, get_weekly_overall
    return get_weekly_galleries(week_start), get_weekly_overall(week_start)


# ── 주 선택 ──────────────────────────────────────────────────────────
weeks = load_week_list()

if not weeks:
    st.markdown(
        f'<h1 style="font-size:1.55rem;font-weight:700;color:{C_TITLE};">📅 주간 리포트</h1>',
        unsafe_allow_html=True,
    )
    st.info("아직 주간 리포트가 없습니다. 분석 봇이 실행된 후 확인해주세요.")
    st.stop()

default_week = st.session_state.get("weekly_week_start", weeks[0])
default_idx  = weeks.index(default_week) if default_week in weeks else 0

with st.sidebar:
    selected_week = st.selectbox(
        "주간 선택",
        options=weeks,
        index=default_idx,
        key="sel_week",
    )
    st.session_state["weekly_week_start"] = selected_week
    st.caption("최신순 목록")


# ── 데이터 ───────────────────────────────────────────────────────────
try:
    galleries_df, overall = load_weekly(selected_week)
except Exception as e:
    st.error(f"데이터 로딩 오류: {e}")
    st.stop()

if galleries_df.empty:
    st.warning(f"**{selected_week}** 주간 데이터가 없습니다.")
    st.stop()

# 게시글 수 많은 순 정렬
records  = sorted(
    galleries_df.to_dict("records"),
    key=lambda r: int(r.get("total_posts", 0) or 0),
    reverse=True,
)
week_end = str(records[0].get("week_end", "")) if records else ""


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<h1 style="font-size:1.55rem;font-weight:700;color:{C_TITLE};'
    f'letter-spacing:-0.03em;margin-bottom:2px;">📅 주간 리포트</h1>',
    unsafe_allow_html=True,
)
st.caption(
    f"{selected_week} ~ {week_end} · 갤러리 {len(records)}개"
    f" · 주간 10건 미만 갤러리는 AI 요약 제외"
)
st.divider()


# ── AI 종합 요약 ──────────────────────────────────────────────────────
if overall and overall.get("ai_summary"):
    st.markdown(
        f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};margin-bottom:6px;">'
        f'✦ AI 종합 요약</div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;color:{C_BODY};line-height:1.78;">'
            f'{str(overall["ai_summary"])}</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)


# ── 갤러리 카드 (2열) ─────────────────────────────────────────────────
st.markdown(
    f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">'
    f'갤러리별 분석</div>',
    unsafe_allow_html=True,
)

pairs = [records[i:i+2] for i in range(0, len(records), 2)]

for pair in pairs:
    cols = st.columns(2)
    for col, r in zip(cols, pair):
        with col:
            name    = str(r.get("gallery_name", ""))
            total   = int(r.get("total_posts", 0) or 0)
            idx     = records.index(r)
            color   = gallery_color(idx)
            ai_text = str(r.get("ai_summary", "") or "")

            kw_raw = r.get("keywords", "[]")
            kws    = json.loads(kw_raw) if isinstance(kw_raw, str) else (kw_raw or [])

            tp_raw = r.get("top_posts", "[]")
            tops   = json.loads(tp_raw) if isinstance(tp_raw, str) else (tp_raw or [])

            dc_raw = r.get("daily_counts", "{}")
            daily_counts = json.loads(dc_raw) if isinstance(dc_raw, str) else (dc_raw or {})

            st.markdown(
                f'<div style="height:4px;background:{color};border-radius:3px;margin-bottom:4px;"></div>',
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                # 헤더: 갤러리명 + 게시글 수
                hc1, hc2 = st.columns([3, 1])
                with hc1:
                    st.markdown(
                        f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};">{name}</div>',
                        unsafe_allow_html=True,
                    )
                with hc2:
                    st.markdown(label_html("TOTAL"), unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="font-size:1.35rem;font-weight:700;color:{C_TITLE};'
                        f'letter-spacing:-0.02em;line-height:1.2;margin-top:4px;">{total:,}건</div>',
                        unsafe_allow_html=True,
                    )

                # 일별 추이 바 차트
                if daily_counts:
                    st.markdown(
                        f'<div style="margin-top:10px;">{label_html("일별 게시글 수")}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(daily_count_bar_html(daily_counts), unsafe_allow_html=True)

                # AI 요약
                if ai_text and not ai_text.startswith("("):
                    st.markdown(
                        f'<div style="margin-top:10px;">{ai_block_html(ai_text)}</div>',
                        unsafe_allow_html=True,
                    )

                # 키워드
                if kws:
                    st.markdown(
                        f'<div style="margin:12px 0 4px;">{label_html("주요 키워드")}</div>',
                        unsafe_allow_html=True,
                    )
                    tags = "".join(kw_tag_html(kw, cnt) for kw, cnt in kws[:8])
                    st.markdown(f'<div style="line-height:2;">{tags}</div>', unsafe_allow_html=True)

                # TOP 5 게시글
                if tops:
                    st.markdown(
                        f'<div style="margin:12px 0 6px;">{label_html("TOP 5 게시글")}</div>',
                        unsafe_allow_html=True,
                    )
                    rows_html = "".join(
                        post_row_html(
                            rank=i + 1,
                            title=p.get("제목", ""),
                            url=p.get("링크", ""),
                            comments=int(p.get("댓글수", 0) or 0),
                            likes=int(p.get("추천수", 0) or 0),
                            views=int(p.get("조회수", 0) or 0),
                            date_str=str(p.get("날짜", ""))[:10],
                        )
                        for i, p in enumerate(tops)
                    )
                    st.markdown(rows_html, unsafe_allow_html=True)
