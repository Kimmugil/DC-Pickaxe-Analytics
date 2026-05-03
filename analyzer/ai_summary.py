"""
Gemini AI 요약 생성

모델: gemini-2.5-flash
용도:
  - 일간 이슈 갤러리 요약 (headline + summary + category_scores + major_issues + sentiment + temperature_tag + issue_cause)
  - 일간 경계 갤러리 짧은 요약
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
    ai_samples: list[dict] | None = None,
) -> dict:
    """
    Returns: {
        headline, summary, temperature_tag, issue_cause,
        category_scores, major_issues, sentiment
    }

    category_scores 키: balance | operation | bug | payment | content
    issue_cause: balance | operation | bug | payment | content | 기타
    """
    kw_str = ", ".join(kw for kw, _ in keywords[:10]) if keywords else "없음"
    ai_samples = ai_samples or []

    # 본문 포함 샘플 게시글 (AI 분석 핵심 입력)
    samples_md = "\n\n".join(
        f"[{i+1}] 제목: {p['제목']}\n"
        f"     댓글: {p['댓글수']}  추천: {p['추천수']}\n"
        f"     본문: {p['본문'] or '(없음)'}"
        for i, p in enumerate(ai_samples)
    )

    # top_posts는 링크 표시용으로만 사용
    top_md = "\n".join(
        f"{i+1}. {p['제목']} — 댓글 {p['댓글수']}, 링크: {p['링크']}"
        for i, p in enumerate(top_posts[:5])
    )

    prompt = f"""당신은 DC인사이드 게임 갤러리 커뮤니티 동향 분석 전문가입니다.

## 분석 대상
갤러리: {gallery_name}
오늘 게시량: {count_today}건  (7일 평균: {avg_7d:.0f}건 / 이슈 점수: {issue_score}/10)
전체 키워드 빈도 (제목 기반): {kw_str}

## 참여도 상위 게시글 샘플 ({len(ai_samples)}개, 본문 포함)
{samples_md}

## 댓글 수 상위 게시글 (링크 참조용)
{top_md}

---

위 데이터를 바탕으로 아래 JSON 형식으로만 응답하세요 (마크다운 코드블록 없이, 순수 JSON만):

{{
  "headline": "오늘 이 갤러리를 한 줄로 표현 (20자 이내)",
  "summary": "3~4문장 상황 서술",
  "temperature_tag": "분위기 한 단어",
  "issue_cause": "balance | operation | bug | payment | content | 기타 중 하나",
  "category_scores": {{
    "balance":   {{"score": 0, "summary": ""}},
    "operation": {{"score": 0, "summary": ""}},
    "bug":       {{"score": 0, "summary": ""}},
    "payment":   {{"score": 0, "summary": ""}},
    "content":   {{"score": 0, "summary": ""}}
  }},
  "major_issues": [
    {{
      "title": "이슈 제목",
      "detail": "2~3줄 설명",
      "mention_count": 0,
      "ref_url": ""
    }}
  ],
  "sentiment": {{
    "positive": "긍정 분위기 요약 (없으면 빈 문자열)",
    "negative": "불만/부정 분위기 요약 (없으면 빈 문자열)"
  }}
}}

## 각 필드 작성 지침

headline (20자 이내):
- 오늘 이 갤러리에서 일어난 일을 뉴스 헤드라인처럼 압축
- 예: "패치 이후 밸런스 논란 폭발", "서버 점검 공지에 유저 반발"

summary (3~4문장):
- 핵심 트리거 → 유저 반응의 성격 → 전반 분위기 순서로 서술
- 왜/어떻게 이슈가 촉발됐는지를 중심으로
- 종결어미 '~습니다/ㅂ니다' 체 통일. 마크다운 금지. 행동 권고 금지

temperature_tag: 오늘 분위기 한 단어 또는 짧은 구 (불만/기대감/논쟁/우려/냉소/환호 등)

issue_cause: 가장 지배적인 이슈 유형 하나만 선택
- balance: 밸런스·스펙·직업·메타 관련 불만/논쟁
- operation: 서버·공지·CS·운영 정책·공식 대응
- bug: 버그·오류·기술적 결함
- payment: 결제·과금·확률·패키지 관련
- content: 신규 컨텐츠·패치·업데이트·이벤트
- 기타: 커뮤니티 자체 이슈 또는 위 분류 해당 없음

category_scores (각 카테고리):
- score: 0~3점 (0=해당 없음, 1=언급 있음, 2=주요 불만, 3=핵심 이슈)
- summary: 해당 카테고리에서 실제로 논의된 내용 1문장. score=0이면 빈 문자열

major_issues (최대 3개):
- title: 이슈 제목 (15자 이내)
- detail: 구체적 설명 2~3문장. 본문 내용 근거로 작성
- mention_count: 해당 이슈를 다루는 게시글 수 (샘플 내 추정)
- ref_url: 가장 대표적인 게시글 링크 (없으면 빈 문자열)

sentiment:
- positive: 긍정적 반응이 있었다면 1~2문장 요약
- negative: 부정적 반응이 있었다면 1~2문장 요약"""

    fallback: dict = {
        "headline": "", "summary": "", "temperature_tag": "", "issue_cause": "기타",
        "category_scores": {
            "balance":   {"score": 0, "summary": ""},
            "operation": {"score": 0, "summary": ""},
            "bug":       {"score": 0, "summary": ""},
            "payment":   {"score": 0, "summary": ""},
            "content":   {"score": 0, "summary": ""},
        },
        "major_issues": [],
        "sentiment": {"positive": "", "negative": ""},
    }
    result = _call_json(prompt, fallback)

    # category_scores 정규화
    cs_raw = result.get("category_scores", {})
    category_scores = {}
    for k in ("balance", "operation", "bug", "payment", "content"):
        raw = cs_raw.get(k, {}) if isinstance(cs_raw, dict) else {}
        category_scores[k] = {
            "score":   int(raw.get("score", 0)),
            "summary": str(raw.get("summary", "")),
        }

    # major_issues 정규화
    raw_issues = result.get("major_issues", [])
    major_issues = []
    for item in (raw_issues if isinstance(raw_issues, list) else [])[:3]:
        major_issues.append({
            "title":         str(item.get("title", "")),
            "detail":        str(item.get("detail", "")),
            "mention_count": int(item.get("mention_count", 0)),
            "ref_url":       str(item.get("ref_url", "")),
        })

    # sentiment 정규화
    raw_sentiment = result.get("sentiment", {})
    sentiment = {
        "positive": str(raw_sentiment.get("positive", "")) if isinstance(raw_sentiment, dict) else "",
        "negative": str(raw_sentiment.get("negative", "")) if isinstance(raw_sentiment, dict) else "",
    }

    # issue_cause: category_scores 중 최고점 카테고리로 override (동점이면 AI 판단 우선)
    ai_cause = str(result.get("issue_cause", "기타"))
    top_cat  = max(category_scores, key=lambda k: category_scores[k]["score"])
    issue_cause = ai_cause if ai_cause != "기타" else (top_cat if category_scores[top_cat]["score"] > 0 else "기타")

    return {
        "headline":        str(result.get("headline", "")),
        "summary":         str(result.get("summary", "")),
        "temperature_tag": str(result.get("temperature_tag", "")),
        "issue_cause":     issue_cause,
        "category_scores": category_scores,
        "major_issues":    major_issues,
        "sentiment":       sentiment,
    }


# ── 일간 경계 갤러리 요약 ─────────────────────────────────────────────

def summarize_daily_borderline(
    gallery_name: str,
    top_posts: list[dict],
    keywords: list[list],
    issue_score: int,
    count_today: int,
    avg_baseline: float,
    ai_samples: list[dict] | None = None,
) -> dict:
    """
    Returns: { summary, temperature_tag }
    경계 갤러리는 본문 샘플을 활용하되 짧은 출력 유지.
    """
    kw_str = ", ".join(kw for kw, _ in keywords[:5]) if keywords else "없음"
    ai_samples = ai_samples or []
    samples_md = "\n".join(
        f"- {p['제목']} (댓글{p['댓글수']}) / {p['본문'][:100] or '(없음)'}"
        for p in ai_samples[:10]
    )
    prompt = f"""DC인사이드 갤러리 동향을 분석하는 어시스턴트입니다.

## 갤러리: {gallery_name}
- 오늘 게시글: {count_today}건 (기준 평균: {avg_baseline:.0f}건, 이슈 점수: {issue_score}/10)
- 주요 키워드: {kw_str}
- 주요 게시글 샘플:
{samples_md}

이 갤러리는 이슈 임계값 바로 아래(경계)입니다. 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):

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


# ── 월간 갤러리별 요약 ────────────────────────────────────────────────

def summarize_monthly_gallery(
    gallery_name: str,
    month: str,
    issue_days: int,
    max_issue_score: int,
    top_cause: str,
    keywords: list[list],
    headlines: list[str],
) -> str:
    kw_str = ", ".join(kw for kw, _ in keywords[:10]) if keywords else "없음"
    headline_md = "\n".join(f"- {h}" for h in headlines[:10]) if headlines else "(없음)"
    cause_map = {
        "balance": "밸런스", "operation": "운영", "bug": "버그",
        "payment": "결제", "content": "컨텐츠",
    }
    cause_ko = cause_map.get(top_cause, top_cause or "기타")
    prompt = f"""DC인사이드 게임 갤러리 월간 동향을 분석하는 어시스턴트입니다.

## 갤러리: {gallery_name} ({month})
- 이슈 발생일: {issue_days}일
- 최고 이슈 점수: {max_issue_score}/10
- 주요 이슈 유형: {cause_ko}
- 주요 키워드: {kw_str}
- 이슈 헤드라인 목록:
{headline_md}

위 데이터를 바탕으로 이 갤러리의 **이번 달 동향 요약**을 3~4문장으로 작성하세요.

조건:
- 한국어로 작성
- 마크다운 헤딩 금지
- 3~4문장 이내
- 이달 주요 이슈의 원인과 커뮤니티 분위기를 중심으로
- 종결어미 '~습니다/ㅂ니다' 체 통일. 행동 권고 금지. 없는 사실 추론 금지"""
    return _call(prompt)


# ── 월간 전체 종합 요약 ───────────────────────────────────────────────

def summarize_monthly_overall(
    gallery_results: list[dict],
    month: str,
) -> str:
    summaries_md = "\n\n".join(
        f"### {r['gallery_name']} (이슈 {r['issue_days']}일, 최고 점수 {r['max_issue_score']}점)\n{r['ai_summary']}"
        for r in gallery_results
        if r.get("ai_summary") and r["ai_summary"] != "(이슈 없음 — AI 요약 제외)"
    )
    if not summaries_md:
        return ""

    gallery_list = ", ".join(r["gallery_name"] for r in gallery_results)
    prompt = f"""키우기 장르 DC인사이드 갤러리들의 월간 동향을 종합 분석하는 어시스턴트입니다.

## 분석 기간: {month}
## 분석 갤러리: {gallery_list}

### 갤러리별 월간 요약
{summaries_md}

위 내용을 바탕으로 **전체 월간 종합 요약**을 작성하세요:
- 이번 달 키우기 장르 전반의 공통 분위기와 주요 화제
- 갤러리별로 두드러진 이슈의 원인과 유저 반응의 특징
- 전반적으로 커뮤니티 정서가 어떤 방향으로 흘렀는지

조건:
- 한국어로 작성
- 마크다운 헤딩은 ## 이하만 사용 (h1 금지)
- 5~7문장 이내
- 원인과 맥락을 포함한 서술
- 사실과 민심을 객관적으로 서술. 행동 제안이나 권고 금지
- 모든 문장은 종결어미를 '~습니다/ㅂ니다' 체로 통일"""
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
