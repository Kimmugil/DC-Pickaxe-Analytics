"""
Gemini AI 요약 생성

모델: gemini-2.5-flash
용도:
  - 일간 이슈 갤러리 요약 (summary + temperature_tag + issue_cause)
  - 주간 갤러리별 요약
  - 주간 전체 종합 요약
"""

from __future__ import annotations
import os
import re
import json as json_mod
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


def _call_json(prompt: str, fallback: dict) -> dict:
    text = _call(prompt)
    # Direct JSON parse
    try:
        return json_mod.loads(text)
    except Exception:
        pass
    # Extract from markdown code block
    m = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if m:
        try:
            return json_mod.loads(m.group(1))
        except Exception:
            pass
    # Extract first JSON object in text
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        try:
            return json_mod.loads(m.group(0))
        except Exception:
            pass
    fallback["_raw"] = text
    return fallback


# ── 일간 이슈 요약 ────────────────────────────────────────────────────

def summarize_daily_issue(
    gallery_name: str,
    top_posts: list[dict],
    keywords: list[list],
    issue_score: int,
    count_today: int,
    avg_7d: float,
) -> dict:
    """
    Returns: { summary, temperature_tag, issue_cause }
    issue_cause: 컨텐츠 | 운영 | 화제 | 기타
    """
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

위 데이터를 바탕으로 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

{{
  "summary": "3~4문장 요약",
  "temperature_tag": "한 단어 또는 짧은 구",
  "issue_cause": "컨텐츠 | 운영 | 화제 | 기타 중 정확히 하나"
}}

각 필드 작성 지침:

summary:
- 단순히 무엇이 있었는지가 아니라 **왜/어떻게** 이슈가 촉발됐는지를 중심으로 서술
- 핵심 트리거(특정 게시글, 사건, 발표 등) → 유저 반응의 성격 → 전반적 분위기 순서로 서술
- 3~4문장, 한국어, 마크다운 금지
- 종결어미 '~습니다/ㅂ니다' 체로 통일 ('~했다', '~이다' 혼용 금지)
- 사실 기반으로 서술. 행동 권고 금지

temperature_tag:
- 이 갤러리의 오늘 분위기를 가장 잘 표현하는 한 단어 또는 짧은 구
- 예시: 불만, 기대감, 논쟁, 우려, 흥분, 실망, 호기심, 논란, 환호, 냉소, 피로감 등
- 예시에 없어도 더 정확한 표현이 있으면 사용

issue_cause:
- 컨텐츠: 게임 컨텐츠/패치/업데이트/밸런스 이슈
- 운영: 서버/공지/결제/CS/운영 정책 관련
- 화제: 외부 사건·유명인·스트리머 관련
- 기타: 커뮤니티 자체 이슈 또는 위 분류에 해당 없음"""

    fallback = {"summary": "", "temperature_tag": "", "issue_cause": "기타"}
    result = _call_json(prompt, fallback)
    return {
        "summary":         str(result.get("summary", "")),
        "temperature_tag": str(result.get("temperature_tag", "")),
        "issue_cause":     str(result.get("issue_cause", "기타")),
    }


# ── 일간 경계 갤러리 요약 ─────────────────────────────────────────────

def summarize_daily_borderline(
    gallery_name: str,
    top_posts: list[dict],
    keywords: list[list],
    issue_score: int,
    count_today: int,
    avg_baseline: float,
) -> dict:
    """
    Returns: { summary, temperature_tag }
    """
    kw_str    = ", ".join(kw for kw, _ in keywords[:5]) if keywords else "없음"
    top_title = top_posts[0]["제목"] if top_posts else "없음"
    prompt = f"""DC인사이드 갤러리 동향을 분석하는 어시스턴트입니다.

## 갤러리: {gallery_name}
- 오늘 게시글: {count_today}건 (기준 평균: {avg_baseline:.0f}건, 이슈 점수: {issue_score}/10)
- 주요 키워드: {kw_str}
- 상위 게시글 제목: {top_title}

이 갤러리는 이슈 임계값 바로 아래입니다. 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

{{
  "summary": "2문장 이내 요약",
  "temperature_tag": "한 단어 또는 짧은 구"
}}

summary: 오늘 주목할 만한 점과 촉발 원인을 간략히. 2문장 이내, 종결어미 '~습니다/ㅂ니다' 체.
temperature_tag: 분위기를 가장 잘 표현하는 한 단어 또는 짧은 구."""

    fallback = {"summary": "", "temperature_tag": ""}
    result = _call_json(prompt, fallback)
    return {
        "summary":         str(result.get("summary", "")),
        "temperature_tag": str(result.get("temperature_tag", "")),
    }


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
1. 이번 주 가장 화제가 된 사건/주제와 그 원인
2. 유저들의 반응과 감정의 결, 특징적인 정서

조건:
- 한국어로 작성
- 마크다운 헤딩(#) 사용 금지
- 3~4문장 이내
- 단순 나열이 아니라 '왜 화제가 됐는지'를 포함해서 서술
- 사실과 민심을 객관적으로 서술. 행동 제안이나 권고 금지. 없는 사실 추론 금지
- 모든 문장은 종결어미를 '~습니다/ㅂ니다' 체로 통일. '~했다', '~이다' 등 해라체 혼용 금지"""
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
- 갤러리별로 두드러진 이슈의 원인과 유저 반응의 특징
- 전반적으로 커뮤니티 정서가 어떤 방향으로 흐르는지

조건:
- 한국어로 작성
- 마크다운 헤딩은 ## 이하만 사용 (h1 금지)
- 5~7문장 이내
- 단순 나열이 아니라 원인과 맥락을 포함
- 사실과 민심을 객관적으로 서술. 행동 제안이나 권고 금지. 실제 데이터에 근거하여 작성
- 모든 문장은 종결어미를 '~습니다/ㅂ니다' 체로 통일. '~했다', '~이다' 등 해라체 혼용 금지"""
    return _call(prompt)
