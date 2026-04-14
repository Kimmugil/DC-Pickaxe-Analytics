"""
DC-Pickaxe Analytics — 홈

구성:
  - 30일 가로 스크롤 캘린더 (📅🚨 클릭 이동)
  - 최신 주간 리포트 갤러리 카드 미리보기
  - 최근 주간 / 일간 리포트 상태 카드 (하단)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="DC-Pickaxe Analytics",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.style import (
    inject_css, render_sidebar_nav,
    gallery_color, label_html, kw_tag_html, ai_block_html,
    C_TITLE, C_HEADING, C_BODY, C_MUTED, C_LABEL, C_BORDER, C_ACCENT,
    C_ISSUE_H, C_ISSUE_M, C_ISSUE_L, C_GREEN,
)
inject_css()
render_sidebar_nav()


# ── 데이터 로드 ──────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_home_data():
    from sheets.reader import get_latest_weekly_info, get_latest_daily_issue_info
    weekly = get_latest_weekly_info()
    daily  = get_latest_daily_issue_info()
    return weekly, daily


@st.cache_data(ttl=300)
def load_latest_weekly_galleries(week_start: str):
    from sheets.reader import get_weekly_galleries, get_weekly_overall
    galleries = get_weekly_galleries(week_start)
    overall   = get_weekly_overall(week_start)
    return galleries, overall


@st.cache_data(ttl=300)
def load_calendar_data():
    from sheets.reader import get_daily_issue_dates, get_weekly_gallery_list
    return set(get_daily_issue_dates()), set(get_weekly_gallery_list())


weekly_meta, daily_meta = load_home_data()


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<h1 style="font-size:1.65rem;font-weight:700;color:{C_TITLE};'
    f'letter-spacing:-0.03em;margin-bottom:2px;">⛏️ DC-Pickaxe Analytics</h1>',
    unsafe_allow_html=True,
)
st.caption("키우기 장르 갤러리 동향 분석 대시보드")
st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)


# ── 캘린더 (가로 스크롤) ─────────────────────────────────────────────
try:
    from datetime import date, timedelta
    issue_dates, week_dates = load_calendar_data()
    today = date.today()
    start = today - timedelta(days=29)  # 30일 전부터

    cells = ""
    cur = start
    while cur <= today:
        d_str    = cur.strftime("%Y-%m-%d")
        day_name = cur.strftime("%a")
        is_today   = cur == today
        has_issue  = d_str in issue_dates
        has_weekly = d_str in week_dates

        bg     = "#4F46E5" if is_today else "#FFFFFF"
        border = "2px solid #4F46E5" if is_today else "1px solid #E2E8F0"
        num_c  = "#FFFFFF" if is_today else "#334155"
        day_c  = "#FFFFFF" if is_today else "#94A3B8"

        markers = ""
        if has_weekly:
            markers += (
                f'<a href="/weekly" target="_self" style="text-decoration:none;'
                f'font-size:0.8rem;line-height:1.2;display:block;">📅</a>'
            )
        if has_issue:
            markers += (
                f'<a href="/daily" target="_self" style="text-decoration:none;'
                f'font-size:0.8rem;line-height:1.2;display:block;">🚨</a>'
            )

        cells += (
            f'<div style="display:inline-flex;flex-direction:column;align-items:center;'
            f'min-width:46px;border:{border};border-radius:8px;padding:5px 4px 6px;'
            f'background:{bg};gap:1px;flex-shrink:0;">'
            f'<div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;color:{day_c};">{day_name}</div>'
            f'<div style="font-size:0.82rem;font-weight:700;color:{num_c};margin:1px 0;">{cur.day}</div>'
            f'<div style="min-height:18px;text-align:center;">{markers}</div>'
            f'</div>'
        )
        cur += timedelta(days=1)

    calendar_html = (
        f'<div style="overflow-x:auto;padding:4px 2px 6px;">'
        f'<div style="display:flex;gap:5px;width:max-content;">{cells}</div>'
        f'</div>'
        f'<div style="font-size:0.71rem;color:#94A3B8;margin-bottom:2px;">'
        f'📅 주간 리포트 &nbsp;·&nbsp; 🚨 일간 이슈 &nbsp;·&nbsp; 클릭하면 해당 페이지로 이동</div>'
    )
    st.markdown(calendar_html, unsafe_allow_html=True)
    st.markdown('<div style="height:6px;"></div>', unsafe_allow_html=True)
except Exception:
    pass


st.divider()


# ── 최신 주간 리포트 미리보기 ────────────────────────────────────────
if weekly_meta:
    ws = weekly_meta["week_start"]
    we = weekly_meta["week_end"]
    st.markdown(
        f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:4px;">'
        f'📅 최신 주간 리포트 — {ws} ~ {we}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="font-size:0.76rem;color:{C_MUTED};margin-bottom:10px;line-height:1.6;">'
        f'주간 게시글 수가 10건 미만인 갤러리는 AI 요약에서 제외됩니다. '
        f'전체 갤러리의 주간 현황 확인은 '
        f'<a href="/weekly" target="_self" style="color:{C_ACCENT};text-decoration:none;font-weight:600;">'
        f'주간 리포트</a>를 확인해 주세요.</div>',
        unsafe_allow_html=True,
    )

    try:
        galleries_df, overall = load_latest_weekly_galleries(ws)

        # 전체 AI 요약
        if overall and overall.get("ai_summary"):
            summary = str(overall["ai_summary"])
            with st.expander("✦ AI 종합 요약 보기", expanded=True):
                st.markdown(
                    f'<div style="font-size:0.88rem;color:{C_BODY};line-height:1.78;">{summary}</div>',
                    unsafe_allow_html=True,
                )

        # 갤러리 카드 2열 (게시글 수 내림차순)
        if not galleries_df.empty:
            records = sorted(
                galleries_df.to_dict("records"),
                key=lambda r: int(r.get("total_posts", 0) or 0),
                reverse=True,
            )
            # 중복 갤러리 제거 (gallery_id 기준 최신 1건만)
            seen = set()
            deduped = []
            for r in records:
                gid = r.get("gallery_id", r.get("gallery_name", ""))
                if gid not in seen:
                    seen.add(gid)
                    deduped.append(r)
            records = deduped

            pairs = [records[i:i+2] for i in range(0, len(records), 2)]
            for pair in pairs:
                cols = st.columns(2)
                for col, r in zip(cols, pair):
                    with col:
                        name    = str(r.get("gallery_name", ""))
                        total   = int(r.get("total_posts", 0) or 0)
                        idx     = records.index(r)
                        color   = gallery_color(idx)

                        kw_raw  = r.get("keywords", "[]")
                        kws     = json.loads(kw_raw) if isinstance(kw_raw, str) else (kw_raw or [])

                        ai_text = str(r.get("ai_summary", "") or "")

                        st.markdown(
                            f'<div style="height:4px;background:{color};border-radius:3px;margin-bottom:2px;"></div>',
                            unsafe_allow_html=True,
                        )
                        with st.container(border=True):
                            # 갤러리명 + 게시글 수
                            hc1, hc2 = st.columns([3, 1])
                            with hc1:
                                st.markdown(
                                    f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};">{name}</div>',
                                    unsafe_allow_html=True,
                                )
                            with hc2:
                                st.markdown(label_html("TOTAL"), unsafe_allow_html=True)
                                st.markdown(
                                    f'<div style="font-size:1.2rem;font-weight:700;color:{C_TITLE};'
                                    f'letter-spacing:-0.02em;line-height:1.2;">{total:,}건</div>',
                                    unsafe_allow_html=True,
                                )

                            # 키워드
                            if kws:
                                tags = "".join(kw_tag_html(kw, cnt) for kw, cnt in kws[:6])
                                st.markdown(
                                    f'<div style="margin:6px 0 2px;">{tags}</div>',
                                    unsafe_allow_html=True,
                                )

                            # AI 요약 (2문장 미리보기)
                            if ai_text and not ai_text.startswith("("):
                                sentences = ai_text.split(". ")
                                short = ". ".join(sentences[:2])
                                if not short.endswith("."):
                                    short += "."
                                st.markdown(
                                    f'<div style="font-size:0.84rem;color:{C_MUTED};line-height:1.68;'
                                    f'margin-top:8px;border-top:1px solid {C_BORDER};padding-top:8px;">'
                                    f'{short}</div>',
                                    unsafe_allow_html=True,
                                )
        else:
            st.info("갤러리별 데이터가 없습니다.")
    except Exception as e:
        st.warning(f"주간 리포트 로딩 실패: {e}")

else:
    st.info("아직 발행된 주간 리포트가 없습니다. 분석 봇을 실행하면 여기에 표시됩니다.")


st.divider()


# ── 최근 리포트 현황 카드 (하단) ─────────────────────────────────────
st.markdown(
    f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">'
    f'📋 최근 리포트 현황</div>',
    unsafe_allow_html=True,
)

col_w, col_d = st.columns(2)

with col_w:
    with st.container(border=True):
        st.markdown(label_html("최근 주간 리포트"), unsafe_allow_html=True)
        if weekly_meta:
            ws = weekly_meta["week_start"]
            we = weekly_meta["week_end"]
            st.markdown(
                f'<div style="font-size:1.3rem;font-weight:700;color:{C_TITLE};'
                f'letter-spacing:-0.02em;line-height:1.25;margin:6px 0 4px;">'
                f'{ws} ~ {we}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:0.78rem;color:{C_MUTED};margin-bottom:10px;">'
                f'주간 리포트 발행 완료</div>',
                unsafe_allow_html=True,
            )
            if st.button("주간 리포트 보기 →", key="btn_weekly", use_container_width=True):
                st.session_state["weekly_week_start"] = ws
                st.switch_page("pages/weekly.py")
        else:
            st.markdown(
                f'<div style="font-size:0.88rem;color:{C_MUTED};padding:8px 0;">'
                f'아직 주간 리포트가 없습니다.</div>',
                unsafe_allow_html=True,
            )

with col_d:
    with st.container(border=True):
        st.markdown(label_html("최근 일간 이슈 리포트"), unsafe_allow_html=True)
        if daily_meta:
            date_str = daily_meta["date"]
            cnt      = daily_meta["issue_gallery_count"]
            st.markdown(
                f'<div style="font-size:1.3rem;font-weight:700;color:{C_TITLE};'
                f'letter-spacing:-0.02em;line-height:1.25;margin:6px 0 4px;">'
                f'{date_str}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:0.78rem;color:{C_MUTED};margin-bottom:10px;">'
                f'이슈 감지 갤러리 <b style="color:{C_HEADING};">{cnt}개</b></div>',
                unsafe_allow_html=True,
            )
            if st.button("일간 이슈 보기 →", key="btn_daily", use_container_width=True):
                st.session_state["daily_date"] = date_str
                st.switch_page("pages/daily.py")
        else:
            st.markdown(
                f'<div style="font-size:0.88rem;color:{C_MUTED};padding:8px 0;">'
                f'최근 이슈 리포트가 없습니다.</div>',
                unsafe_allow_html=True,
            )
