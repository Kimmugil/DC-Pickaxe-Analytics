"""
Gemini AI 요약 모듈
- 일간 이슈 요약 (이슈가 있는 갤러리만)
- 주간 갤러리별 요약
- 주간 종합 요약 (주목할 게임 + 관찰포인트 + 주요 게시글 링크)
"""
import os
import time
import pandas as pd
from google import genai
from typing import List, Dict

MIN_POSTS_FOR_AI = 5


def _get_client():
    return genai.Client(api_key=os.environ['GEMINI_API_KEY'])


def _generate(prompt: str, max_retries: int = 3) -> str:
    client = _get_client()
    model  = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=model, contents=prompt).text.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"    Gemini 재시도 {attempt+1}/{max_retries} ({wait}s): {e}")
                time.sleep(wait)
            else:
                return f"[AI 생성 실패: {e}]"
    return ''


# ── 일간 이슈 요약 ────────────────────────────────────────────────────

def summarize_gallery_issue(
    posts_df: pd.DataFrame,
    gallery_name: str,
    stats: dict,
    keywords: list,
    game_signals: dict,
    top5_posts: list,
) -> str:
    """
    이슈가 탐지된 갤러리의 이슈 내용을 요약합니다.
    이슈가 없는 갤러리는 이 함수를 호출하지 않습니다.
    """
    new_7d = stats.get('new_posts_7d', 0)
    if posts_df.empty or new_7d < MIN_POSTS_FOR_AI:
        return f"> 분석 데이터 부족 ({new_7d}건)"

    kw_text = ', '.join(f"{kw}({cnt})" for kw, cnt in keywords[:10])

    signal_lines = []
    for sig_data in game_signals.values():
        if isinstance(sig_data, dict) and sig_data.get('ratio', 0) >= 5:
            signal_lines.append(f"- {sig_data.get('label','')}: {sig_data['ratio']}%")
    signals_text = '\n'.join(signal_lines) if signal_lines else '- 특이 신호 없음'

    top_text = '\n'.join(
        f"[추천{p.get('추천수',0)}/댓글{p.get('댓글수',0)}] {p.get('제목','')}"
        for p in top5_posts
    )

    prompt = f"""당신은 디씨인사이드 커뮤니티 분석 전문가입니다.
'{gallery_name}' 갤러리에서 오늘 이슈가 탐지되었습니다.

[신호]
{signals_text}

[오늘 주요 키워드]
{kw_text}

[이슈 관련 상위 게시글]
{top_text}

아래 형식으로 이슈 내용을 한국어 마크다운으로 작성하세요. 200자 이내.

### 이슈 요약
(2~3문장: 어떤 이슈가 발생했는지 핵심만)

### 원인 추정
(1~2문장: 왜 이슈가 생겼는지)"""

    return _generate(prompt)


# ── 주간 갤러리 요약 ──────────────────────────────────────────────────

def summarize_weekly_gallery(
    gallery_name: str,
    week_start: str,
    week_end: str,
    total_posts: int,
    keywords: list,
    top5_posts: list,
) -> str:
    """갤러리별 주간 요약을 생성합니다."""
    if total_posts < MIN_POSTS_FOR_AI:
        return f"> 주간 게시글 부족 ({total_posts}건)"

    kw_text = ', '.join(f"{kw}({cnt})" for kw, cnt in keywords[:10])
    top_text = '\n'.join(
        f"[추천{p.get('추천수',0)}/댓글{p.get('댓글수',0)}] {p.get('제목','')}"
        for p in top5_posts
    )

    prompt = f"""당신은 디씨인사이드 커뮤니티 분석 전문가입니다.
'{gallery_name}' 갤러리의 {week_start}~{week_end} 주간 요약입니다.

[주간 통계]
- 주간 게시글: {total_posts}건

[주요 키워드]
{kw_text}

[주간 인기 게시글]
{top_text}

아래 형식으로 200자 이내로 작성하세요.

### 주간 흐름
(2문장: 이번 주 전반적인 활동 흐름)

### 주요 관심사
(1문장: 유저들이 가장 집중한 주제)"""

    return _generate(prompt)


# ── 주간 종합 요약 ────────────────────────────────────────────────────

def summarize_weekly_overview(
    gallery_results: List[Dict],
    week_start: str,
    week_end: str,
) -> str:
    """
    전체 갤러리의 주간 종합 요약을 생성합니다.
    주목할 게임 + 관찰포인트(각 포인트별 관련 게시글 링크 포함) 구조.
    """
    import json as _json

    active = [r for r in gallery_results if r.get('total_posts_week', 0) >= MIN_POSTS_FOR_AI]
    if not active:
        return "> 이번 주 분석 가능한 갤러리가 없습니다."

    gallery_blocks = []
    for r in active:
        name     = r['gallery_name']
        total    = r.get('total_posts_week', 0)
        summary  = str(r.get('ai_gallery_weekly', ''))[:200]
        keywords = r.get('top_keywords', [])
        if isinstance(keywords, str):
            try:
                keywords = _json.loads(keywords)
            except Exception:
                keywords = []
        kw_text = ', '.join(kw for kw, _ in keywords[:5])

        # 갤러리별 top5 posts with links
        top5 = r.get('top5_posts', [])
        if isinstance(top5, str):
            try:
                top5 = _json.loads(top5)
            except Exception:
                top5 = []
        posts_lines = []
        for p in top5[:3]:
            link  = p.get('링크', '')
            title = p.get('제목', '(제목없음)')
            rec   = p.get('추천수', 0)
            cmt   = p.get('댓글수', 0)
            if link:
                posts_lines.append(f"  - [{title}]({link}) (추천{rec}/댓글{cmt})")
            else:
                posts_lines.append(f"  - {title} (추천{rec}/댓글{cmt})")

        posts_text = '\n'.join(posts_lines) if posts_lines else '  (게시글 없음)'
        gallery_blocks.append(
            f"### {name} (주간 {total}건)\n"
            f"키워드: {kw_text}\n"
            f"요약: {summary}\n"
            f"주요 게시글:\n{posts_text}"
        )

    combined = '\n\n'.join(gallery_blocks)

    prompt = f"""당신은 한국 키우기 게임 커뮤니티 트렌드 분석 전문가입니다.
{week_start}~{week_end} 한 주간 각 갤러리 데이터입니다.

{combined}

아래 마크다운 형식으로 정확히 작성하세요.
- 모든 갤러리에 동등한 비중 (게시글 수 기준 아님)
- 링크는 반드시 마크다운 형식 [제목](URL) 으로 유지
- 서론/결론 불필요, 형식 이외 추가 텍스트 금지

## 주목할 게임
(2~3문장: 이번 주 독특한 이슈·사건이 있었던 게임과 이유)

## 이번 주 관찰포인트

### 1. (관찰포인트 제목)
(1~2문장 설명)
관련 게시글: (위 데이터에서 이 포인트와 관련된 게시글 링크를 [제목](URL) 형식으로 1~2개)

### 2. (관찰포인트 제목)
(1~2문장 설명)
관련 게시글: (위 데이터에서 이 포인트와 관련된 게시글 링크를 [제목](URL) 형식으로 1~2개)

### 3. (관찰포인트 제목) — 선택사항
(1~2문장 설명)
관련 게시글: (위 데이터에서 이 포인트와 관련된 게시글 링크를 [제목](URL) 형식으로 1~2개)"""

    return _generate(prompt)


# ── 하위호환 (기존 코드에서 import 하는 경우) ─────────────────────────
def summarize_gallery(posts_df, gallery_name, stats, keywords, game_signals) -> str:
    """하위호환용. summarize_gallery_issue를 래핑합니다."""
    top5 = []
    return summarize_gallery_issue(posts_df, gallery_name, stats, keywords, game_signals, top5)


def summarize_all_galleries(gallery_results: list) -> str:
    """하위호환용. 빈 문자열 반환 (주간 요약으로 대체됨)."""
    return ''
