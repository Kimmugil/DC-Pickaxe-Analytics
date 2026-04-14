"""
DC-Pickaxe Analytics — 분석 방법
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="분석 방법 — DC-Pickaxe",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dashboard.style import (
    inject_css, render_sidebar_nav, card_spacer,
    C_TITLE, C_HEADING, C_BODY, C_MUTED, C_LABEL, C_BORDER,
    C_ACCENT, C_ISSUE_H, C_ISSUE_M, C_ISSUE_L,
)
inject_css()
render_sidebar_nav()


# ── 페이지 헤더 ──────────────────────────────────────────────────────
st.markdown(
    f'<h1 style="font-size:1.55rem;font-weight:700;color:{C_TITLE};'
    f'letter-spacing:-0.03em;margin-bottom:2px;">📖 분석 방법</h1>',
    unsafe_allow_html=True,
)
st.caption("DC-Pickaxe Analytics 데이터 수집 · 분석 기준 · 이슈 판별 방식 안내")
st.divider()


# ════════════════════════════════════════════════════════════════════
# 1. 데이터 파이프라인
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">🔄 데이터 파이프라인</div>',
    unsafe_allow_html=True,
)

pipeline_html = f"""
<div style="display:flex;gap:0;align-items:stretch;margin-bottom:16px;flex-wrap:wrap;gap:4px;">
  <div style="flex:1;min-width:120px;background:#EEF2FF;border:1px solid #C7D2FE;border-radius:8px;
              padding:14px 16px;text-align:center;">
    <div style="font-size:1.3rem;margin-bottom:4px;">🕷️</div>
    <div style="font-size:0.82rem;font-weight:700;color:{C_ACCENT};">스크래핑 봇</div>
    <div style="font-size:0.73rem;color:{C_MUTED};margin-top:3px;line-height:1.5;">DC Inside<br>갤러리 게시글 수집</div>
  </div>
  <div style="display:flex;align-items:center;font-size:1.2rem;color:{C_LABEL};padding:0 4px;">→</div>
  <div style="flex:1;min-width:120px;background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;
              padding:14px 16px;text-align:center;">
    <div style="font-size:1.3rem;margin-bottom:4px;">📊</div>
    <div style="font-size:0.82rem;font-weight:700;color:#059669;">Google Sheets</div>
    <div style="font-size:0.73rem;color:{C_MUTED};margin-top:3px;line-height:1.5;">갤러리별 시트<br>원본 데이터 저장</div>
  </div>
  <div style="display:flex;align-items:center;font-size:1.2rem;color:{C_LABEL};padding:0 4px;">→</div>
  <div style="flex:1;min-width:120px;background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;
              padding:14px 16px;text-align:center;">
    <div style="font-size:1.3rem;margin-bottom:4px;">⚙️</div>
    <div style="font-size:0.82rem;font-weight:700;color:#92400E;">분석 엔진</div>
    <div style="font-size:0.73rem;color:{C_MUTED};margin-top:3px;line-height:1.5;">이슈 감지 / 주간 집계<br>키워드 · AI 요약</div>
  </div>
  <div style="display:flex;align-items:center;font-size:1.2rem;color:{C_LABEL};padding:0 4px;">→</div>
  <div style="flex:1;min-width:120px;background:#FDF4FF;border:1px solid #E9D5FF;border-radius:8px;
              padding:14px 16px;text-align:center;">
    <div style="font-size:1.3rem;margin-bottom:4px;">📈</div>
    <div style="font-size:0.82rem;font-weight:700;color:#7C3AED;">대시보드</div>
    <div style="font-size:0.73rem;color:{C_MUTED};margin-top:3px;line-height:1.5;">리포트 시각화<br>결과 확인</div>
  </div>
</div>
"""
st.markdown(pipeline_html, unsafe_allow_html=True)
st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════
# 2. 데이터 수집
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">🕷️ 데이터 수집</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">수집 대상</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
            f'• <b>플랫폼</b>: DC Inside 마이너 갤러리<br>'
            f'• <b>장르</b>: 키우기 관련 게임 갤러리 전체<br>'
            f'• <b>수집 주기</b>: GitHub Actions 스케줄 (매일 새벽)<br>'
            f'• <b>수집 범위</b>: 갤러리별 전체 게시글 목록 페이지'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

with col2:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">수집 필드</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
            f'• <b>제목</b>: 게시글 제목<br>'
            f'• <b>날짜</b>: 작성 일시 (당일 게시글은 HH:MM 형식)<br>'
            f'• <b>댓글수</b>: 댓글 수<br>'
            f'• <b>추천수</b>: 좋아요/추천 수<br>'
            f'• <b>조회수</b>: 조회 수<br>'
            f'• <b>링크</b>: 게시글 직접 URL'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

st.markdown(
    f'<div style="font-size:0.76rem;color:{C_MUTED};margin:4px 0 16px;line-height:1.6;">'
    f'⚠️ DC Inside 특성상 당일 올라온 게시글의 날짜 필드는 "03:11"(시간만 표시) 형식으로 수집됩니다. '
    f'분석 시 인접 행의 날짜를 참조하여 자동 추론합니다.'
    f'</div>',
    unsafe_allow_html=True,
)
st.divider()


# ════════════════════════════════════════════════════════════════════
# 3. 일간 이슈 분석
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">🚨 일간 이슈 분석</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.75;margin-bottom:12px;">'
    f'매일 각 갤러리의 당일 게시글을 분석하여 <b>최근 7일 평균 대비 비정상적 활동</b>을 감지합니다. '
    f'단순한 게시량 증가만으로는 이슈가 발행되지 않으며, '
    f'<b>실질적 반응(댓글·추천)이 동반된 경우에만</b> 이슈로 판정됩니다.'
    f'</div>',
    unsafe_allow_html=True,
)

score_col1, score_col2 = st.columns(2)

with score_col1:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">'
            f'① 게시량 급증 점수 <span style="font-size:0.73rem;color:{C_MUTED};font-weight:400;">(비율 × 절대 증분 복합)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        rows = [
            ("3배 이상 + 절대 +20건 이상", "+4점"),
            ("2.5배 이상 + 절대 +10건 이상", "+3점"),
            ("2배 이상 + 절대 +5건 이상", "+2점"),
            ("1.5배 이상 + 절대 +3건 이상", "+1점"),
        ]
        for cond, pts in rows:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid {C_BORDER};">'
                f'<span style="font-size:0.82rem;color:{C_BODY};">{cond}</span>'
                f'<span style="font-size:0.82rem;font-weight:700;color:{C_ACCENT};">{pts}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div style="font-size:0.73rem;color:{C_MUTED};margin-top:8px;line-height:1.5;">'
            f'비율만 높아도 절대 증가폭이 작으면 점수 없음.<br>'
            f'(예: 평균 2건 → 오늘 5건 = 2.5배지만 +3건 → 조건 미달)'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

with score_col2:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">'
            f'② 단일 게시글 화제성 점수'
            f'</div>',
            unsafe_allow_html=True,
        )
        rows2 = [
            ("댓글 50개 이상", "+3점"),
            ("댓글 30개 이상", "+2점"),
            ("댓글 15개 이상", "+1점"),
            ("추천 20개 이상", "+2점"),
            ("추천 10개 이상", "+1점"),
        ]
        for cond, pts in rows2:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid {C_BORDER};">'
                f'<span style="font-size:0.82rem;color:{C_BODY};">{cond}</span>'
                f'<span style="font-size:0.82rem;font-weight:700;color:{C_ACCENT};">{pts}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin:10px 0 8px;">'
            f'③ 바이럴 확산 점수 <span style="font-size:0.73rem;color:{C_MUTED};font-weight:400;">(화제 게시글 수)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        rows3 = [
            ("댓글 10+ 게시글이 5개 이상", "+2점"),
            ("댓글 10+ 게시글이 3개 이상", "+1점"),
        ]
        for cond, pts in rows3:
            st.markdown(
                f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:5px 0;border-bottom:1px solid {C_BORDER};">'
                f'<span style="font-size:0.82rem;color:{C_BODY};">{cond}</span>'
                f'<span style="font-size:0.82rem;font-weight:700;color:{C_ACCENT};">{pts}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        card_spacer(10)

# 이슈 임계값
st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
threshold_html = f"""
<div style="display:flex;gap:12px;flex-wrap:wrap;">
  <div style="flex:1;min-width:180px;background:{C_ISSUE_H}12;border:1px solid {C_ISSUE_H};
              border-radius:8px;padding:12px 16px;">
    <div style="font-size:0.73rem;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;color:{C_ISSUE_H};margin-bottom:4px;">🔴 고심도 이슈</div>
    <div style="font-size:1.1rem;font-weight:700;color:{C_ISSUE_H};">7점 이상</div>
    <div style="font-size:0.78rem;color:{C_MUTED};margin-top:4px;">대규모 활동 급증 + 바이럴 확산</div>
  </div>
  <div style="flex:1;min-width:180px;background:{C_ISSUE_M}12;border:1px solid {C_ISSUE_M};
              border-radius:8px;padding:12px 16px;">
    <div style="font-size:0.73rem;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;color:{C_ISSUE_M};margin-bottom:4px;">🟡 중심도 이슈</div>
    <div style="font-size:1.1rem;font-weight:700;color:{C_ISSUE_M};">4 ~ 6점</div>
    <div style="font-size:0.78rem;color:{C_MUTED};margin-top:4px;">상당한 활동 증가 또는 화제 게시글 존재</div>
  </div>
  <div style="flex:1;min-width:180px;background:#F1F5F9;border:1px solid {C_BORDER};
              border-radius:8px;padding:12px 16px;">
    <div style="font-size:0.73rem;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;color:{C_LABEL};margin-bottom:4px;">⚪ 이슈 없음</div>
    <div style="font-size:1.1rem;font-weight:700;color:{C_MUTED};">4점 미만</div>
    <div style="font-size:0.78rem;color:{C_MUTED};margin-top:4px;">일상적 활동 범위 내</div>
  </div>
</div>
"""
st.markdown(threshold_html, unsafe_allow_html=True)
st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
st.markdown(
    f'<div style="font-size:0.76rem;color:{C_MUTED};margin:8px 0 0;line-height:1.6;">'
    f'💡 <b>이슈 감지 임계값: 5점 이상</b>. 점수가 5점 이상인 갤러리만 이슈 리포트에 포함되며 AI 요약이 생성됩니다.'
    f'</div>',
    unsafe_allow_html=True,
)
st.divider()


# ════════════════════════════════════════════════════════════════════
# 4. 주간 리포트 분석
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">📅 주간 리포트 분석</div>',
    unsafe_allow_html=True,
)

col_w1, col_w2 = st.columns(2)

with col_w1:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">집계 기준</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
            f'• <b>기간</b>: 월요일 ~ 일요일 (7일)<br>'
            f'• <b>실행 시점</b>: 매주 월요일 새벽 (전주 마감)<br>'
            f'• <b>집계 단위</b>: 갤러리별 주간 전체 게시글<br>'
            f'• <b>일별 추이</b>: 요일별 게시글 수 바 차트<br>'
            f'• <b>키워드</b>: 제목 기반 TF-IDF 상위 10개'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

with col_w2:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">AI 요약 제외 조건</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
            f'• 주간 게시글 수 <b>10건 미만</b> 갤러리<br>'
            f'• 데이터가 너무 적으면 AI 요약의 신뢰도가 낮아지기 때문<br>'
            f'• <b>단, 분석 자체는 진행</b>됩니다 (일별 추이, 키워드, TOP5 게시글 표시)<br>'
            f'• 0건 갤러리도 "활동 없음"으로 카드에 표시됨'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

st.divider()


# ════════════════════════════════════════════════════════════════════
# 5. AI 요약 생성
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">✦ AI 요약 생성</div>',
    unsafe_allow_html=True,
)

col_a1, col_a2 = st.columns(2)

with col_a1:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">일간 이슈 AI 요약</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
            f'• <b>모델</b>: Google Gemini API<br>'
            f'• <b>입력</b>: 이슈 갤러리의 TOP 5 게시글 제목 + 키워드 + 이슈 점수<br>'
            f'• <b>출력</b>: 갤러리 분위기 및 주요 이슈 1~2문장 요약<br>'
            f'• <b>생성 조건</b>: 이슈 점수 5점 이상 갤러리만'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

with col_a2:
    with st.container(border=True):
        st.markdown(
            f'<div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};margin-bottom:8px;">주간 AI 요약</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
            f'• <b>갤러리별 요약</b>: 주간 TOP5 게시글 + 키워드 기반 1~2문장<br>'
            f'• <b>종합 요약</b>: 전체 갤러리 동향을 묶어 3~5문장으로 정리<br>'
            f'• <b>제외</b>: 주간 10건 미만 갤러리 (AI 요약 품질 보장)<br>'
            f'• <b>활용</b>: 홈 화면 "AI 종합 요약" + 주간 리포트 상세 페이지'
            f'</div>',
            unsafe_allow_html=True,
        )
        card_spacer(10)

st.divider()


# ════════════════════════════════════════════════════════════════════
# 6. 키워드 추출
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">🏷️ 키워드 추출</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown(
        f'<div style="font-size:0.84rem;color:{C_BODY};line-height:1.8;">'
        f'• <b>대상</b>: 각 갤러리 게시글 제목 전체<br>'
        f'• <b>방식</b>: 형태소 분석 기반 명사 추출 → 빈도 기준 정렬<br>'
        f'• <b>불용어 제거</b>: 게임명, 조사, 일반 부사 등 의미 없는 단어 필터링<br>'
        f'• <b>출력</b>: (키워드, 출현 횟수) 쌍으로 최대 10개 표시<br>'
        f'• <b>표시 위치</b>: 갤러리 카드 키워드 태그 영역'
        f'</div>',
        unsafe_allow_html=True,
    )
    card_spacer(10)

st.divider()


# ════════════════════════════════════════════════════════════════════
# 7. 실행 스케줄
# ════════════════════════════════════════════════════════════════════
st.markdown(
    f'<div style="font-size:1.05rem;font-weight:700;color:{C_HEADING};margin-bottom:10px;">⏰ 실행 스케줄</div>',
    unsafe_allow_html=True,
)

schedule_html = f"""
<div style="display:flex;gap:10px;flex-wrap:wrap;">
  <div style="flex:1;min-width:160px;background:#F8FAFC;border:1px solid {C_BORDER};
              border-radius:8px;padding:14px 16px;">
    <div style="font-size:0.73rem;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;color:{C_LABEL};margin-bottom:6px;">🕷️ 스크래핑</div>
    <div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};">매일 오전 2시</div>
    <div style="font-size:0.78rem;color:{C_MUTED};margin-top:4px;line-height:1.5;">
      DC Inside 갤러리 게시글 수집<br>→ Google Sheets 저장
    </div>
  </div>
  <div style="flex:1;min-width:160px;background:#F8FAFC;border:1px solid {C_BORDER};
              border-radius:8px;padding:14px 16px;">
    <div style="font-size:0.73rem;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;color:{C_LABEL};margin-bottom:6px;">🚨 일간 분석</div>
    <div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};">매일 오전 3시</div>
    <div style="font-size:0.78rem;color:{C_MUTED};margin-top:4px;line-height:1.5;">
      전일 게시글 이슈 점수 산출<br>이슈 갤러리 AI 요약 생성
    </div>
  </div>
  <div style="flex:1;min-width:160px;background:#F8FAFC;border:1px solid {C_BORDER};
              border-radius:8px;padding:14px 16px;">
    <div style="font-size:0.73rem;font-weight:700;letter-spacing:0.06em;
                text-transform:uppercase;color:{C_LABEL};margin-bottom:6px;">📅 주간 분석</div>
    <div style="font-size:0.88rem;font-weight:700;color:{C_HEADING};">매주 월요일 오전 4시</div>
    <div style="font-size:0.78rem;color:{C_MUTED};margin-top:4px;line-height:1.5;">
      전주(월~일) 갤러리별 집계<br>AI 갤러리 요약 + 종합 요약
    </div>
  </div>
</div>
"""
st.markdown(schedule_html, unsafe_allow_html=True)
st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)
