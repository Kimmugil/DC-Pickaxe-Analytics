"""
디씨곡괭이 정련소 — 홈

구성:
  - 30일 가로 스크롤 캘린더 (📅📌 클릭 이동, 오늘 자동 포커스)
  - 최근 일간 체크포인트 3건 카드
  - 최신 주간 리포트 풀 디테일 (막대그래프 포함)
  - 최근 리포트 상태 카드 (하단)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="디씨곡괭이 정련소",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.style import (
    inject_css, render_sidebar_nav, card_spacer,
    gallery_color, label_html, kw_tag_html, ai_block_html,
    daily_count_bar_html, issue_badge_html, post_row_html,
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


@st.cache_data(ttl=300)
def load_recent_issues():
    from sheets.reader import get_daily_issues
    df = get_daily_issues(n=30)
    if df.empty:
        return []
    if "issue_score" in df.columns:
        df["issue_score"] = pd.to_numeric(df["issue_score"], errors="coerce").fillna(0).astype(int)
    return df.head(3).to_dict("records")


weekly_meta, daily_meta = load_home_data()


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<h1 style="font-size:1.65rem;font-weight:700;color:{C_TITLE};'
    f'letter-spacing:-0.03em;margin-bottom:2px;">⛏️ 디씨곡괭이 정련소</h1>',
    unsafe_allow_html=True,
)
st.caption("키우기 장르 갤러리 동향 분석 대시보드")
st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)


# ── 캘린더 (가로 스크롤, 오늘 자동 포커스) ─────────────────────────────
try:
    from datetime import date, timedelta
    issue_dates, week_dates = load_calendar_data()
    today = date.today()
    start = today - timedelta(days=29)

    MONTH_KO = ["","1월","2월","3월","4월","5월","6월","7월","8월","9월","10월","11월","12월"]

    cells = ""
    cur = start
    prev_month = None
    while cur <= today:
        d_str    = cur.strftime("%Y-%m-%d")
        day_name = cur.strftime("%a")
        is_today   = cur == today
        has_issue  = d_str in issue_dates
        has_weekly = d_str in week_dates

        # 월 바뀔 때 구분 라벨 삽입
        if cur.month != prev_month:
            cells += (
                f'<div style="display:inline-flex;flex-direction:column;justify-content:center;'
                f'align-items:center;min-width:26px;padding:0 2px;flex-shrink:0;">'
                f'<div style="font-size:0.65rem;font-weight:700;color:#94A3B8;'
                f'writing-mode:vertical-rl;text-orientation:mixed;letter-spacing:0.04em;">'
                f'{MONTH_KO[cur.month]}</div>'
                f'</div>'
            )
            prev_month = cur.month

        bg     = "#4F46E5" if is_today else "#FFFFFF"
        border = "2px solid #4F46E5" if is_today else "1px solid #E2E8F0"
        num_c  = "#FFFFFF" if is_today else "#334155"
        day_c  = "#FFFFFF" if is_today else "#94A3B8"
        today_attr = ' id="cal-today"' if is_today else ""

        markers = ""
        if has_weekly:
            markers += (
                f'<a href="/weekly?week_start={d_str}" target="_parent" style="text-decoration:none;'
                f'font-size:0.8rem;line-height:1.2;display:block;">📅</a>'
            )
        if has_issue:
            markers += (
                f'<a href="/daily?date={d_str}" target="_parent" style="text-decoration:none;'
                f'font-size:0.8rem;line-height:1.2;display:block;">📌</a>'
            )

        cells += (
            f'<div{today_attr} style="display:inline-flex;flex-direction:column;align-items:center;'
            f'min-width:46px;border:{border};border-radius:8px;padding:5px 4px 6px;'
            f'background:{bg};gap:1px;flex-shrink:0;">'
            f'<div style="font-size:0.6rem;font-weight:600;text-transform:uppercase;color:{day_c};">{day_name}</div>'
            f'<div style="font-size:0.82rem;font-weight:700;color:{num_c};margin:1px 0;">{cur.day}</div>'
            f'<div style="min-height:18px;text-align:center;">{markers}</div>'
            f'</div>'
        )
        cur += timedelta(days=1)

    cal_html = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8">
<style>
  body{{margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:transparent;overflow:hidden;}}
  a{{text-decoration:none;}}
  #cal-scroll{{overflow-x:auto;padding:4px 2px 4px;scrollbar-width:thin;scrollbar-color:#CBD5E1 transparent;}}
  #cal-scroll::-webkit-scrollbar{{height:4px;}}
  #cal-scroll::-webkit-scrollbar-track{{background:transparent;}}
  #cal-scroll::-webkit-scrollbar-thumb{{background:#CBD5E1;border-radius:2px;}}
</style>
</head><body>
<div id="cal-scroll">
  <div style="display:flex;gap:5px;width:max-content;">{cells}</div>
</div>
<script>
  (function(){{
    var c=document.getElementById('cal-scroll');
    var t=document.getElementById('cal-today');
    if(c&&t) c.scrollLeft=Math.max(0,t.offsetLeft-c.clientWidth/2+t.offsetWidth/2);
  }})();
</script>
</body></html>"""

    components.html(cal_html, height=90, scrolling=False)

    # 범례 — iframe 밖에서 별도 렌더링 (잘림 방지)
    st.markdown(
        f'<div style="font-size:0.71rem;color:#94A3B8;margin-top:2px;margin-bottom:2px;'
        f'padding:3px 0;">'
        f'📅 주간 리포트 &nbsp;·&nbsp; 📌 일간 체크포인트 &nbsp;·&nbsp; 클릭하면 해당 페이지로 이동'
        f'</div>',
        unsafe_allow_html=True,
    )
except Exception:
    pass


st.divider()


# ── 최근 일간 체크포인트 (최신 3건 카드) ───────────────────────────────
st.markdown(
    f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};margin-bottom:4px;">'
    f'📌 최근 일간 체크포인트</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f'<div style="font-size:0.76rem;color:{C_MUTED};margin-bottom:10px;line-height:1.6;">'
    f'이슈 점수는 <b>게시량 급증</b>(최대 4점) · <b>게시글 화제성</b>(댓글·추천, 최대 5점) · '
    f'<b>바이럴 확산</b>(화제 게시글 복수, 최대 2점) 합산입니다. '
    f'<b>5점 이상</b>인 날에만 발행됩니다.</div>',
    unsafe_allow_html=True,
)

try:
    recent_issues = load_recent_issues()
    if recent_issues:
        issue_cols = st.columns(3)
        for col, r in zip(issue_cols, recent_issues):
            with col:
                name     = str(r.get("gallery_name", ""))
                date_str = str(r.get("date", ""))
                score    = int(r.get("issue_score", 0) or 0)
                ai_text  = str(r.get("ai_summary", "") or "")

                with st.container(border=True):
                    st.markdown(label_html(date_str), unsafe_allow_html=True)
                    st.markdown(
                        f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};'
                        f'margin:4px 0 6px;">{name}</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(issue_badge_html(score), unsafe_allow_html=True)
                    if ai_text:
                        sentences = ai_text.split(". ")
                        short = ". ".join(sentences[:2])
                        if not short.endswith("."):
                            short += "."
                        st.markdown(
                            f'<div style="font-size:0.82rem;color:{C_MUTED};line-height:1.65;'
                            f'margin-top:8px;border-top:1px solid {C_BORDER};padding-top:8px;">'
                            f'{short}</div>',
                            unsafe_allow_html=True,
                        )
                    card_spacer(8)
                    if st.button(
                        "체크포인트 상세보기 →",
                        key=f"issue_{date_str}_{name}",
                        use_container_width=True,
                    ):
                        st.session_state["daily_selected_date"] = date_str
                        st.switch_page("pages/daily.py")
                    card_spacer(8)
    else:
        st.info("최근 발행된 체크포인트가 없습니다.")
except Exception:
    st.info("체크포인트 데이터를 불러올 수 없습니다.")


st.divider()


# ── 최신 주간 리포트 (풀 디테일) ────────────────────────────────────────
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
        f'주간 게시글 수가 10건 미만인 갤러리는 AI 요약에서 제외됩니다.</div>',
        unsafe_allow_html=True,
    )

    try:
        galleries_df, overall = load_latest_weekly_galleries(ws)

        # 전체 AI 종합 요약
        if overall and overall.get("ai_summary"):
            summary = str(overall["ai_summary"])
            with st.expander("✦ AI 종합 요약 보기", expanded=True):
                st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div style="font-size:0.88rem;color:{C_BODY};line-height:1.78;'
                    f'padding:0 6px;">{summary}</div>',
                    unsafe_allow_html=True,
                )
                card_spacer(12)

        # 갤러리 카드 2열 (게시글 수 내림차순)
        if not galleries_df.empty:
            records = sorted(
                galleries_df.to_dict("records"),
                key=lambda r: int(r.get("total_posts", 0) or 0),
                reverse=True,
            )
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
                        ai_text = str(r.get("ai_summary", "") or "")

                        kw_raw = r.get("keywords", "[]")
                        kws    = json.loads(kw_raw) if isinstance(kw_raw, str) else (kw_raw or [])

                        tp_raw = r.get("top_posts", "[]")
                        tops   = json.loads(tp_raw) if isinstance(tp_raw, str) else (tp_raw or [])

                        dc_raw = r.get("daily_counts", "{}")
                        daily_counts = json.loads(dc_raw) if isinstance(dc_raw, str) else (dc_raw or {})

                        with st.container(border=True):
                            hc1, hc2 = st.columns([3, 1])
                            with hc1:
                                st.markdown(
                                    f'<div style="font-size:0.95rem;font-weight:700;color:{C_HEADING};'
                                    f'display:flex;align-items:center;gap:7px;">'
                                    f'<span style="display:inline-block;width:9px;height:9px;'
                                    f'border-radius:50%;background:{color};flex-shrink:0;"></span>'
                                    f'{name}</div>',
                                    unsafe_allow_html=True,
                                )
                            with hc2:
                                st.markdown(label_html("TOTAL"), unsafe_allow_html=True)
                                st.markdown(
                                    f'<div style="font-size:1.2rem;font-weight:700;color:{C_TITLE};'
                                    f'letter-spacing:-0.02em;line-height:1.2;">{total:,}건</div>',
                                    unsafe_allow_html=True,
                                )

                            if daily_counts:
                                st.markdown(
                                    f'<div style="margin-top:10px;">{label_html("일별 게시글 수")}</div>',
                                    unsafe_allow_html=True,
                                )
                                st.markdown(daily_count_bar_html(daily_counts), unsafe_allow_html=True)

                            if ai_text and not ai_text.startswith("("):
                                st.markdown(
                                    f'<div style="margin-top:10px;">{ai_block_html(ai_text)}</div>',
                                    unsafe_allow_html=True,
                                )

                            if kws:
                                st.markdown(
                                    f'<div style="margin:12px 0 4px;">{label_html("주요 키워드")}</div>',
                                    unsafe_allow_html=True,
                                )
                                tags = "".join(kw_tag_html(kw, cnt) for kw, cnt in kws[:8])
                                st.markdown(f'<div style="line-height:2;">{tags}</div>', unsafe_allow_html=True)

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

                            card_spacer(12)
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
        card_spacer(8)

with col_d:
    with st.container(border=True):
        st.markdown(label_html("최근 일간 체크포인트"), unsafe_allow_html=True)
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
            if st.button("체크포인트 보기 →", key="btn_daily", use_container_width=True):
                st.session_state["daily_date"] = date_str
                st.switch_page("pages/daily.py")
        else:
            st.markdown(
                f'<div style="font-size:0.88rem;color:{C_MUTED};padding:8px 0;">'
                f'최근 체크포인트가 없습니다.</div>',
                unsafe_allow_html=True,
            )
        card_spacer(8)
