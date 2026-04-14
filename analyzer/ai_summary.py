"""
Gemini AI 요약 생성

모델: gemini-2.5-flash
용도:
  - 일간 이슈 갤러리 요약
  - 주간 갤러리별 요약
  - 주간 전체 종합 요약
"""

from __future__ import annotations
import os
from google import genai

_MODEL = "gemini-2.5-flash"
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    return _client


def _call(prompt: str) -> str:
    resp = _get_client().models.generate_content(model=_MODEL, contents=prompt)
    return resp.text.strip()


# ── 일간 이슈 요약 ────────────────────────────────────────────────────

def summarize_daily_issue(
    gallery_name: str,
    top_posts: list[dict],
    keywords: list[list],
    issue_score: int,
    count_today: int,
    avg_7d: float,
) -> str:
    kw_str   = ", ".join(kw for kw, _ in keywords[:8]) if keywords else "없음"
    posts_md = "\n".join(
        f"{i+1}. [{p['제목']}]({p['링크']}) — 댓글 {p['댓글수']}, 추천 {p['추천수']}, 조회 {p['조회수']}"
        for i, p in enumerate(top_posts[:5])
    )
    prompt = f"""DC인사이드 갤러리 동향을 분석하는 어시스턴트입니다.

## 갤러리: {gallery_name}
- 오늘 게시글: {count_today}건 (7일 평균: {avg_7d:.0f}건, 이슈 점수: {issue_score}/10)
- 주요 키워드: {kw_str}
- 상위 게시글:
{posts_md}

위 데이터를 바탕으로 **3~4문장** 요약을 작성하세요:
1. 오늘 이 갤러리에서 무슨 일이 있었는지 (핵심 사건/화제)
2. 유저 반응의 성격과 분위기 (불만/기대/논쟁 등)

조건:
- 한국어로 작성
- 마크다운 헤딩(#) 사용 금지
- 3~4문장 이내
- 사실과 민심을 객관적으로 서술. 행동 제안이나 권고 금지"""
    return _call(prompt)


# ── 주간 갤러리별 요약 ────────────────────────────────────────────────

def summarize_weekly_gallery(
    gallery_name: str,
    total_posts: int,
    top_posts: list[dict],
    keywords: list[list],
    week_start: str,
    week_end: str,
) -> str:
    kw_str   = ", ".join(kw for kw, _ in keywords[:8]) if keywords else "없음"
    posts_md = "\n".join(
        f"{i+1}. [{p['제목']}]({p['링크']}) — 댓글 {p['댓글수']}, 추천 {p['추천수']}"
        for i, p in enumerate(top_posts[:5])
    )
    prompt = f"""DC인사이드 갤러리 주간 동향을 분석하는 어시스턴트입니다.

## 갤러리: {gallery_name} ({week_start} ~ {week_end})
- 주간 총 게시글: {total_posts}건
- 주요 키워드: {kw_str}
- 인기 게시글 TOP 5:
{posts_md}

위 데이터를 바탕으로 **3~4문장** 주간 요약을 작성하세요:
1. 이번 주 이 갤러리의 주요 화제와 분위기
2. 유저들의 관심사와 반응의 특징

조건:
- 한국어로 작성
- 마크다운 헤딩(#) 사용 금지
- 3~4문장 이내
- 사실과 민심을 객관적으로 서술. 행동 제안이나 권고 금지. 없는 사실 추론 금지"""
    return _call(prompt)


# ── 주간 전체 종합 요약 ───────────────────────────────────────────────

def summarize_weekly_overall(
    gallery_results: list[dict],
    week_start: str,
    week_end: str,
) -> str:
    summaries_md = "\n\n".join(
        f"### {r['gallery_name']} ({r['total_posts']}건)\n{r['ai_summary']}"
        for r in gallery_results
        if r.get("ai_summary") and r["ai_summary"] != "(게시글 부족 — 요약 생략)"
    )
    if not summaries_md:
        return ""

    gallery_list = ", ".join(r["gallery_name"] for r in gallery_results)
    prompt = f"""키우기 장르 DC인사이드 갤러리들의 주간 동향을 종합 분석하는 어시스턴트입니다.

## 분석 기간: {week_start} ~ {week_end}
## 분석 갤러리: {gallery_list}

### 갤러리별 주간 요약
{summaries_md}

위 내용을 바탕으로 **전체 종합 요약**을 작성하세요:
- 이번 주 키우기 장르 전반의 공통 분위기와 주요 화제
- 갤러리별로 두드러진 유저 반응의 특징

조건:
- 한국어로 작성
- 마크다운 헤딩은 ## 이하만 사용 (h1 금지)
- 5~7문장 이내
- 사실과 민심을 객관적으로 서술. 행동 제안이나 권고 금지. 실제 데이터에 근거하여 작성"""
    return _call(prompt)
