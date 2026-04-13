"""
DC-Pickaxe Analytics 디자인 시스템 v7
사이드바 CSS + 캘린더 HTML (inline style) 만 담당
나머지는 Streamlit 네이티브 컴포넌트로 처리
"""

GALLERY_COLORS = [
    '#0F172A', '#334155', '#64748B', '#94A3B8',
    '#1E293B', '#475569', '#7C8FA3', '#B0BEC5',
]

# 사이드바 다크 테마 CSS — Streamlit 프레임워크 요소만 대상
SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: 1px solid #1E293B;
}
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] strong { color: #F1F5F9 !important; }
[data-testid="stSidebar"] hr { border-color: #1E293B !important; opacity: 1; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div {
    background: #1E293B !important;
    border-color: #334155 !important;
}
[data-testid="stSidebar"] button {
    background: #1E293B !important;
    color: #CBD5E1 !important;
    border: 1px solid #334155 !important;
    border-radius: 10px !important;
}
[data-testid="stSidebar"] button:hover {
    background: #334155 !important;
    border-color: #E8A020 !important;
}
</style>
"""


def inject_css() -> None:
    import streamlit as st
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)


def gallery_color(index: int) -> str:
    return GALLERY_COLORS[index % len(GALLERY_COLORS)]


def issue_sev_label(score: int) -> str:
    if score >= 7:
        return '🔴 고'
    elif score >= 4:
        return '🟡 중'
    return '⚫ 저'


def issue_sev_color(score: int) -> str:
    if score >= 7:
        return '#EF4444'
    elif score >= 4:
        return '#F59E0B'
    return '#94A3B8'


def kw_tag(kw: str, cnt: int) -> str:
    return (
        f'<span style="display:inline-block;background:#F1F5F9;border:1px solid #E2E8F0;'
        f'border-radius:6px;padding:2px 8px;font-size:0.75rem;color:#334155;margin:2px 3px 2px 0;">'
        f'{kw} <b style="color:#94A3B8">{cnt}</b></span>'
    )


# 캘린더 HTML — 인라인 스타일만 사용
def calendar_html(year: int, month: int, cal_data: dict, today) -> str:
    import calendar
    from datetime import date
    cal_obj    = calendar.monthcalendar(year, month)
    month_name = f"{year}년 {month}월"
    dows = ''.join(
        f'<div style="text-align:center;font-size:0.7rem;font-weight:700;'
        f'color:#94A3B8;padding:4px 0;">{d}</div>'
        for d in ['월', '화', '수', '목', '금', '토', '일']
    )
    cells = []
    for week in cal_obj:
        for day in week:
            if day == 0:
                cells.append('<div></div>')
                continue
            d           = date(year, month, day)
            d_str       = d.strftime('%Y-%m-%d')
            today_ring  = 'outline:2px solid #E8A020;outline-offset:-2px;' if d == today else ''
            report_type = cal_data.get(d_str)
            if report_type:
                nav_type = 'weekly' if report_type in ('weekly', 'both') else 'daily'
                badge_bg = '#E8A020' if report_type in ('weekly', 'both') else '#475569'
                badge_tx = '주' if report_type == 'weekly' else ('주+일' if report_type == 'both' else '일')
                badge    = (f'<span style="font-size:0.55rem;font-weight:700;padding:1px 4px;'
                            f'border-radius:3px;margin-top:2px;background:{badge_bg};color:white;">'
                            f'{badge_tx}</span>')
                cells.append(
                    f'<div style="aspect-ratio:1;display:flex;flex-direction:column;align-items:center;'
                    f'justify-content:center;border-radius:8px;background:#FEF3C7;min-height:34px;{today_ring}">'
                    f'<a href="?nav_date={d_str}&nav_type={nav_type}" '
                    f'style="text-decoration:none;color:#0F172A;font-weight:700;font-size:0.82rem;'
                    f'display:flex;flex-direction:column;align-items:center;width:100%;height:100%;'
                    f'justify-content:center;">{day}{badge}</a></div>'
                )
            else:
                cells.append(
                    f'<div style="aspect-ratio:1;display:flex;align-items:center;justify-content:center;'
                    f'border-radius:8px;font-size:0.82rem;color:#475569;min-height:34px;{today_ring}">{day}</div>'
                )
    grid = ''.join(cells)
    return (
        f'<div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:14px;'
        f'padding:14px 16px;box-shadow:0 1px 4px rgba(0,0,0,.05);">'
        f'<div style="font-size:0.9rem;font-weight:700;color:#0F172A;margin-bottom:10px;">{month_name}</div>'
        f'<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:3px;">'
        f'{dows}{grid}</div></div>'
    )


# 분석 방법론 마크다운 — 네이티브 st.markdown 으로 렌더링
METHODOLOGY_DAILY_TEMPLATE = """
**분석 기준일:** `{date}`

---

#### 데이터 수집
| 항목 | 내용 |
|:---|:---|
| 24h 수집 범위 | {date} 00:00 ~ 23:59 |
| 맥락 데이터 | 최근 7일 인기글 최대 15건 |
| AI 분석 최대 | 80건 (engagement score 내림차순) |

#### Engagement Score (TOP 5 선정)
```
추천수 × 2 + 댓글수 × 3 + 조회수 × 0.05
```

#### 이슈 점수 산출
| 조건 | 점수 |
|:---|:---:|
| 게임 신호 비율 5% 이상 | +1점 |
| 게임 신호 비율 10% 이상 | +3점 |
| 1위 게시글 댓글 15건 초과 | +1점 |
| 1위 게시글 댓글 30건 초과 | +2점 |
| 1위 게시글 추천 7건 초과 | +1점 |
| 1위 게시글 추천 15건 초과 | +2점 |
| 24h 게시량 7일 일평균 2배 초과 | +2점 |

**이슈 판정 기준:** 총점 **3점 이상**

| 점수 | 심각도 |
|:---:|:---|
| 7점↑ | 🔴 고 |
| 4~6점 | 🟡 중 |
| 3점 | ⚫ 저 |

#### 게임 신호 (9종)
패치·업데이트·공략 수요·컨텐츠 소진·과금 민심·버그·이벤트·밸런스·신규유입·엔드게임 키워드 패턴 매칭

#### 키워드 추출
kiwipiepy 한국어 형태소 분석 — 일반명사·고유명사·외래어, 2자 이상, 불용어 제외

#### AI 요약
Gemini 2.5 Flash — 이슈 판정 갤러리에 한해 생성 (비용 절감)
"""

METHODOLOGY_WEEKLY_TEMPLATE = """
**분석 기간:** `{week_start}` (월) ~ `{week_end}` (일) · 7일

---

#### 데이터 수집
| 항목 | 내용 |
|:---|:---|
| 수집 범위 | 해당 기간 갤러리 전체 게시글 |
| 근거 | stats 탭 날짜별 카운트 기준 |

#### Engagement Score (TOP 5 선정)
```
추천수 × 2 + 댓글수 × 3 + 조회수 × 0.05
```

#### 일별 추이 정규화
각 갤러리의 일별 **최대값 = 100** 기준 상대 지수
→ 갤러리 간 절대 규모 차이 무관하게 활동 패턴 비교 가능

#### 키워드 추출
kiwipiepy 한국어 형태소 분석 — 일반명사·고유명사·외래어, 2자 이상, 불용어 제외

#### AI 요약
Gemini 2.5 Flash
- 갤러리별 주간 요약 + 전체 종합 요약 **2단계** 생성
- 최소 **5건 이상** 게시글 갤러리만 AI 요약 생성
"""
