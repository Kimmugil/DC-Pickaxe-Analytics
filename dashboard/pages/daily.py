"""
DC-Pickaxe Analytics — 일간 이슈 리포트
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="일간 이슈 — DC-Pickaxe",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.style import (
    inject_css, render_sidebar_nav,
    gallery_color, label_html, kw_tag_html, ai_block_html,
    post_row_html, issue_badge_html,
    C_TITLE, C_HEADING, C_BODY, C_MUTED, C_LABEL, C_BORDER,
    C_ISSUE_H, C_ISSUE_M, C_ISSUE_L, C_GREEN,
)
inject_css()
render_sidebar_nav()


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_issue_dates() -> list[str]:
    from sheets.reader import get_daily_issue_dates
    return get_daily_issue_dates()


@st.cache_data(ttl=120)
def load_daily(date_str: str):
    from sheets.reader import get_daily_issues_by_date
    return get_daily_issues_by_date(date_str)


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<h1 style="font-size:1.55rem;font-weight:700;color:{C_TITLE};'
    f'letter-spacing:-0.03em;margin-bottom:2px;">🚨 일간 이슈 리포트</h1>',
    unsafe_allow_html=True,
)

dates = load_issue_dates()

if not dates:
    st.info("아직 이슈 리포트가 없습니다. 이슈 감지 시 자동으로 발행됩니다.")
    st.stop()


# ── 목록 vs 상세 라우팅 ──────────────────────────────────────────────
selected_date = st.session_state.get("daily_selected_date", None)

# ── 목록 화면 ────────────────────────────────────────────────────────
if selected_date is None:
    st.caption(f"총 {len(dates)}건의 이슈 리포트")
    st.divider()

    for date in dates:
        try:
            df = load_daily(date)
            records = df.to_dict("records")
            issue_rows = [r for r in records if str(r.get("has_issue", "0")) == "1"]
            issue_count = len(issue_rows)
            issue_names = ", ".join(str(r.get("gallery_name", "")) for r in issue_rows[:3])
            if len(issue_rows) > 3:
                issue_names += f" 외 {len(issue_rows)-3}개"
        except Exception:
            issue_count = 0
            issue_names = ""

        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 4, 1])
            with c1:
                st.markdown(
                    f'<div style="font-size:1.05rem;font-weight:700;color:{C_TITLE};">{date}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f'<div style="font-size:0.88rem;color:{C_MUTED};padding:4px 0;">'
                    f'이슈 갤러리 <b style="color:{C_HEADING};">{issue_count}개</b>'
                    + (f' &nbsp;·&nbsp; {issue_names}' if issue_names else '') +
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c3:
                if st.button("보기 →", key=f"view_{date}", use_container_width=True):
                    st.session_state["daily_selected_date"] = date
                    st.rerun()

    st.stop()


# ── 상세 화면 ────────────────────────────────────────────────────────
if st.button("← 목록으로"):
    st.session_state["daily_selected_date"] = None
    st.rerun()

try:
    df = load_daily(selected_date)
except Exception as e:
    st.error(f"데이터 로딩 오류: {e}")
    st.stop()

if df.empty:
    st.warning(f"**{selected_date}** 데이터가 없습니다.")
    st.stop()

# 게시글 수 많은 순 정렬
records    = sorted(df.to_dict("records"), key=lambda r: int(r.get("posts_total", 0) or 0), reverse=True)
issue_rows = [r for r in records if str(r.get("has_issue", "0")) == "1"]
all_rows   = records

st.caption(
    f"{selected_date} · "
    f"이슈 감지: **{len(issue_rows)}개** 갤러리 / "
    f"전체 분석: {len(all_rows)}개"
)
st.divider()


# ── 이슈 요약 테이블 ──────────────────────────────────────────────────
if issue_rows:
    st.markdown(
        f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">'
        f'이슈 감지 갤러리</div>',
        unsafe_allow_html=True,
    )

    hcols = st.columns([2, 1, 1, 1])
    for c, t in zip(hcols, ["갤러리", "오늘 게시글", "7일 평균", "이슈 점수"]):
        with c:
            st.markdown(label_html(t), unsafe_allow_html=True)

    for r in sorted(issue_rows, key=lambda x: int(x.get("issue_score", 0) or 0), reverse=True):
        name  = str(r.get("gallery_name", ""))
        total = int(r.get("posts_total", 0) or 0)
        avg   = float(r.get("avg_7d", 0) or 0)
        score = int(r.get("issue_score", 0) or 0)
        rc    = st.columns([2, 1, 1, 1])
        with rc[0]:
            st.markdown(
                f'<div style="font-size:0.88rem;font-weight:600;color:{C_HEADING};padding:4px 0;">{name}</div>',
                unsafe_allow_html=True,
            )
        with rc[1]:
            st.markdown(
                f'<div style="font-size:0.88rem;color:{C_BODY};padding:4px 0;">{total:,}건</div>',
                unsafe_allow_html=True,
            )
        with rc[2]:
            st.markdown(
                f'<div style="font-size:0.88rem;color:{C_MUTED};padding:4px 0;">{avg:.0f}건</div>',
                unsafe_allow_html=True,
            )
        with rc[3]:
            st.markdown(issue_badge_html(score), unsafe_allow_html=True)

    st.divider()


# ── 이슈 갤러리 상세 카드 ────────────────────────────────────────────
if issue_rows:
    st.markdown(
        f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">'
        f'갤러리별 상세</div>',
        unsafe_allow_html=True,
    )

sorted_issues = sorted(issue_rows, key=lambda x: int(x.get("issue_score", 0) or 0), reverse=True)
pairs = [sorted_issues[i:i+2] for i in range(0, len(sorted_issues), 2)]

for pair in pairs:
    cols = st.columns(2)
    for col, r in zip(cols, pair):
        with col:
            name    = str(r.get("gallery_name", ""))
            total   = int(r.get("posts_total", 0) or 0)
            avg     = float(r.get("avg_7d", 0) or 0)
            score   = int(r.get("issue_score", 0) or 0)
            ai_text = str(r.get("ai_summary", "") or "")
            idx     = sorted_issues.index(r)
            color   = gallery_color(idx)

            kw_raw = r.get("keywords", "[]")
            kws    = json.loads(kw_raw) if isinstance(kw_raw, str) else (kw_raw or [])

            tp_raw = r.get("top_posts", "[]")
            tops   = json.loads(tp_raw) if isinstance(tp_raw, str) else (tp_raw or [])

            st.markdown(
                f'<div style="height:4px;background:{color};border-radius:3px;margin-bottom:4px;"></div>',
                unsafe_allow_html=True,
            )

            with st.container(border=True):
                hc1, hc2 = st.columns([3, 2])
                with hc1:
                    st.markdown(
                        f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};">{name}</div>',
                        unsafe_allow_html=True,
                    )
                with hc2:
                    st.markdown(issue_badge_html(score), unsafe_allow_html=True)

                mc1, mc2 = st.columns(2)
                with mc1:
                    st.markdown(label_html("오늘 게시글"), unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="font-size:1.5rem;font-weight:700;color:{C_TITLE};'
                        f'letter-spacing:-0.02em;line-height:1.2;margin:4px 0 10px;">{total:,}건</div>',
                        unsafe_allow_html=True,
                    )
                with mc2:
                    st.markdown(label_html("7일 평균"), unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="font-size:1.5rem;font-weight:700;color:{C_MUTED};'
                        f'letter-spacing:-0.02em;line-height:1.2;margin:4px 0 10px;">{avg:.0f}건</div>',
                        unsafe_allow_html=True,
                    )

                # AI 요약 (메트릭 바로 아래)
                if ai_text:
                    st.markdown(
                        f'<div style="margin-top:4px;">{ai_block_html(ai_text)}</div>',
                        unsafe_allow_html=True,
                    )

                if kws:
                    st.markdown(
                        f'<div style="margin:10px 0 4px;">{label_html("주요 키워드")}</div>',
                        unsafe_allow_html=True,
                    )
                    tags = "".join(kw_tag_html(kw, cnt) for kw, cnt in kws[:8])
                    st.markdown(f'<div style="line-height:2;">{tags}</div>', unsafe_allow_html=True)

                if tops:
                    st.markdown(
                        f'<div style="margin:12px 0 6px;">{label_html("이슈 관련 게시글")}</div>',
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


# ── 이슈 없는 갤러리 요약 (접힘) ─────────────────────────────────────
non_issue = [r for r in all_rows if str(r.get("has_issue", "0")) != "1"]
if non_issue:
    with st.expander(f"이슈 없는 갤러리 ({len(non_issue)}개)"):
        hcols = st.columns([2, 1, 1])
        for c, t in zip(hcols, ["갤러리", "오늘 게시글", "7일 평균"]):
            with c:
                st.markdown(label_html(t), unsafe_allow_html=True)
        for r in non_issue:
            rc = st.columns([2, 1, 1])
            with rc[0]:
                st.markdown(
                    f'<div style="font-size:0.84rem;color:{C_BODY};padding:3px 0;">'
                    f'{r.get("gallery_name", "")}</div>',
                    unsafe_allow_html=True,
                )
            with rc[1]:
                st.markdown(
                    f'<div style="font-size:0.84rem;color:{C_BODY};padding:3px 0;">'
                    f'{int(r.get("posts_total", 0) or 0):,}건</div>',
                    unsafe_allow_html=True,
                )
            with rc[2]:
                st.markdown(
                    f'<div style="font-size:0.84rem;color:{C_MUTED};padding:3px 0;">'
                    f'{float(r.get("avg_7d", 0) or 0):.0f}건</div>',
                    unsafe_allow_html=True,
                )
