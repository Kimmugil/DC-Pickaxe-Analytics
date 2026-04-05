"""
Gemini AI 요약 모듈
- 갤러리별 개별 요약 + 전체 갤러리 크로스 분석 요약
- 모델: gemini-2.5-flash (환경변수 GEMINI_MODEL로 변경 가능)
- SDK: google-genai (신규 통합 SDK)
- 재시도 로직 포함 (지수 백오프)
"""
import os
import time
import pandas as pd
from google import genai
from typing import List, Dict

# 최근 7일 게시글이 이 수치 미만이면 AI 요약 대신 안내 메시지로 대체
MIN_POSTS_FOR_AI = 5


def _get_client():
    return genai.Client(api_key=os.environ['GEMINI_API_KEY'])


def _generate(prompt: str, max_retries: int = 3) -> str:
    """재시도 로직이 포함된 Gemini API 호출."""
    client = _get_client()
    model_name = os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"    Gemini API 오류 (재시도 {attempt + 1}/{max_retries}, {wait}초 대기): {e}")
                time.sleep(wait)
            else:
                print(f"    Gemini API 최종 실패: {e}")
                return f"[AI 요약 생성 실패: {e}]"
    return ''


def summarize_gallery(
    posts_df: pd.DataFrame,
    gallery_name: str,
    stats: dict,
    keywords: list,
    game_signals: dict,
) -> str:
    """
    갤러리별 AI 요약을 생성합니다.

    Args:
        posts_df: 분석 대상 게시글 DataFrame (선택이유 컬럼 포함)
        gallery_name: 갤러리명
        stats: analyze_post_trends + analyze_activity 결과 합산 dict
        keywords: [(키워드, 빈도수), ...] 리스트
        game_signals: analyze_gaming_signals 결과 dict

    Returns:
        마크다운 형식의 요약 문자열
    """
    # ── 게시글 수 부족 시 AI 호출 없이 안내 메시지 반환 ──────────────
    new_7d = stats.get('new_posts_7d', 0)
    total  = stats.get('total_posts', 0)

    if posts_df.empty or new_7d < MIN_POSTS_FOR_AI:
        if new_7d == 0:
            return (
                f"> ⚠️ 최근 7일간 신규 게시글이 없습니다. "
                f"갤러리 활동이 중단됐거나 수집이 아직 이뤄지지 않았을 수 있습니다. "
                f"(누적 게시글: {total:,}건)"
            )
        return (
            f"> ⚠️ 기간 내 신규 작성된 게시글이 너무 적어 ({new_7d}건) "
            f"정확한 유저 동향 분석이 어렵습니다. "
            f"아래 수집된 데이터를 직접 참고해주세요."
        )

    # 분석기준일(24h) 게시글과 맥락용(7일) 게시글 분리
    day_df = posts_df[posts_df.get('선택이유', pd.Series()) == '분석기준일(24h)'] if '선택이유' in posts_df.columns else posts_df
    ctx_df = posts_df[posts_df.get('선택이유', pd.Series()) == '최근7일인기글(참고)'] if '선택이유' in posts_df.columns else pd.DataFrame()

    # 24h 게시글 중 인게이지먼트 상위 30개
    score_col = '_score'
    day_df = day_df.copy()
    day_df[score_col] = day_df['추천수'] * 2 + day_df['댓글수']
    top_day = day_df.nlargest(30, score_col)

    def fmt_posts(df: pd.DataFrame) -> str:
        lines = []
        for _, row in df.iterrows():
            title = str(row.get('제목', ''))
            body  = str(row.get('본문', ''))[:100].replace('\n', ' ')
            lines.append(
                f"[추천{row.get('추천수', 0)}/댓글{row.get('댓글수', 0)}] {title}"
                + (f" | {body}" if body else '')
            )
        return '\n'.join(lines)

    day_posts_text = fmt_posts(top_day)
    ctx_posts_text = fmt_posts(ctx_df.head(10)) if not ctx_df.empty else '(없음)'

    keywords_text = ', '.join([f"{kw}({cnt})" for kw, cnt in keywords[:15]])

    alert_lines = []
    for sig_data in game_signals.values():
        if isinstance(sig_data, dict) and sig_data.get('ratio', 0) >= 5:
            alert_lines.append(f"- {sig_data.get('label', '')}: {sig_data['ratio']}%")
    signals_text = '\n'.join(alert_lines) if alert_lines else '- 특이 신호 없음'

    prompt = f"""당신은 디씨인사이드 커뮤니티 분석 전문가입니다.
아래는 '{gallery_name}' 갤러리의 최근 게시글 데이터입니다.

[통계]
- 총 게시글: {stats.get('total_posts', 0):,}개
- 분석기준일(24h) 신규: {stats.get('new_posts_today', 0):,}개
- 최근 7일: {stats.get('new_posts_7d', 0):,}개
- 피크 시간대: {stats.get('peak_hour', 0)}시

[자주 등장한 키워드]
{keywords_text if keywords_text else '(없음)'}

[주목할 신호]
{signals_text}

[분석기준일(24h) 주요 게시글 — 이것이 핵심 분석 대상입니다]
{day_posts_text if day_posts_text else '(없음)'}

[최근 7일 인기글 — 맥락 참고용]
{ctx_posts_text}

위 데이터를 바탕으로 아래 항목을 한국어 마크다운으로 작성하세요.
분석기준일(24h) 게시글을 중심으로 분석하고, 7일 인기글은 맥락 파악에만 활용하세요.
항목 외의 불필요한 서론·결론은 쓰지 마세요.

### 🔥 오늘의 주요 이슈
(2~3문장: 갤러리에서 가장 화제가 된 사건·주제)

### 💬 민심 흐름
(1~2문장: 유저들의 전반적인 감정 상태, 주요 불만 또는 호감 포인트)

### 🎯 유저 관심사
(1~2문장: 유저들이 가장 집중하는 게임 내 요소 또는 콘텐츠)

### ⚠️ 특이 동향
(있을 경우만 기술. 없으면 "없음"으로 표기)

총 분량: 200~400자"""

    return _generate(prompt)


def summarize_all_galleries(gallery_results: List[Dict]) -> str:
    """
    전체 갤러리를 종합하는 크로스 분석 요약을 생성합니다.

    Args:
        gallery_results: 각 갤러리의 분석 결과 dict 리스트

    Returns:
        마크다운 형식의 종합 요약 문자열
    """
    active_results   = [r for r in gallery_results if r.get('new_posts_7d', 0) >= MIN_POSTS_FOR_AI]
    inactive_results = [r for r in gallery_results if r.get('new_posts_7d', 0) < MIN_POSTS_FOR_AI]

    # 활성 갤러리가 하나도 없으면 종합 요약 불가
    if not active_results:
        names = ', '.join(r['gallery_name'] for r in gallery_results)
        return (
            f"> ⚠️ 오늘 분석 대상 갤러리({names}) 모두 최근 7일 신규 게시글이 "
            f"{MIN_POSTS_FOR_AI}건 미만이어서 종합 동향 분석이 어렵습니다."
        )

    # 갤러리별 요약 블록 — 게시글 수와 관계없이 동등한 비중으로 제공
    gallery_blocks = []
    for result in active_results:
        summary_snippet = str(result.get('ai_summary', ''))[:400]
        gallery_blocks.append(
            f"**{result['gallery_name']}** "
            f"(24h 신규:{result.get('new_posts_today', 0)}건 / "
            f"7일 신규:{result.get('new_posts_7d', 0)}건)\n"
            f"{summary_snippet}"
        )

    # 비활성 갤러리는 별도 언급
    inactive_note = ''
    if inactive_results:
        inactive_names = ', '.join(r['gallery_name'] for r in inactive_results)
        inactive_note = f"\n\n(※ 데이터 부족으로 분석에서 제외된 갤러리: {inactive_names})"

    combined = '\n\n---\n\n'.join(gallery_blocks) + inactive_note

    prompt = f"""당신은 한국 모바일·PC 키우기 게임 커뮤니티 트렌드 분석 전문가입니다.
아래는 오늘 수집된 여러 키우기 게임 갤러리들의 분석 요약입니다.

{combined}

위 내용을 종합하여 아래 항목을 한국어 마크다운으로 작성하세요.

[분석 원칙]
- 모든 갤러리에 동등한 비중을 두세요. 게시글 수가 많다고 더 중요하게 다루지 마세요.
- 갤러리 간 공통으로 나타나는 패턴을 우선 포착하세요.
- 항목 외의 불필요한 서론·결론은 쓰지 마세요.

## 📊 오늘의 키우기 장르 전체 동향
(3~4문장: 여러 갤러리에 걸쳐 공통적으로 나타나는 이슈 또는 흐름)

## 🏆 주목할 게임
(2~3문장: 오늘 특히 독특한 이슈·사건·신규 콘텐츠가 있는 게임과 그 구체적인 이유.
유저 수나 게시글 수가 아닌 이슈의 특이성·영향력 기준으로 선정)

## 👀 이번 주 관찰 포인트
(bullet 2~3개: 여러 갤러리에서 공통으로 보이는 트렌드, 또는 특정 갤러리에서
유독 폭발적으로 나타나는 단일 이슈 중 앞으로 주목해볼 신호)

총 분량: 250~450자"""

    return _generate(prompt)
