"""Gemini 요약. 호출은 call_json() 한 곳, 프롬프트는 이 파일에 모아둠.
- 고정된 분류(밸런스·운영 등)를 쓰지 않는다: AI가 글에서 실제로 보이는 '주제'에 직접 이름을 붙인다.
- AI가 센 숫자(언급 수 등)는 믿지 않고 코드가 다시 계산한다. 근거 글번호는 코드가 검증한다."""
import json
import re
import time

from core import config, db
from . import polish

STYLE = ("종결어미는 '~습니다/ㅂ니다' 체로 통일. 마크다운 금지. 행동 권고 금지. 입력에 없는 사실을 지어내지 말 것. "
         "'대혼란·폭발·참사' 같은 과장 표현을 쓰지 말고 게시량·댓글 수 등 입력에 있는 수치와 사실 중심으로 차분하게 서술. "
         "글에 적힌 내용을 사실처럼 단정하지 말고 '~라는 글이 올라왔다', '유저들은 ~라고 말했다'처럼 출처를 밝혀 쓰고, "
         "원인·의도·앞으로의 일에 대한 유저의 짐작은 '~라는 추측이 많았다'로 사실과 구분할 것. 제목만으로 공식 여부를 단정하지 말 것.")
NO_TAXONOMY = ("주제는 미리 정해진 분류에 끼워 맞추지 말고, 아래 글들에서 실제로 보이는 것만 직접 이름을 붙이세요. "
               "(예: 특정 업데이트 반응, 방송·인물 논란, 공략·정보 공유, 경쟁작 비교, 이벤트 후기 등 — 글에 없는 주제를 추측해 넣지 말 것)")


class AIUnavailable(RuntimeError):
    pass


class AI:
    def __init__(self, conn):
        if not config.GEMINI_API_KEY:
            raise AIUnavailable("GEMINI_API_KEY 가 없습니다 (.env)")
        from google import genai
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.conn = conn
        self.map = polish.load_map(conn)
        self.model = db.setting(conn, "ai.model")
        self.gap = db.setting(conn, "ai.call_gap_sec")
        self.budget = db.setting(conn, "ai.max_calls_per_run")
        self.calls = 0

    def call_json(self, prompt: str) -> dict:
        if self.calls >= self.budget:
            raise AIUnavailable(f"이번 실행의 AI 호출 한도({self.budget}회)에 도달")
        last = None
        for attempt in range(3):
            if self.calls or attempt:
                time.sleep(self.gap * (attempt + 1))
            try:
                self.calls += 1
                resp = self.client.models.generate_content(
                    model=self.model, contents=prompt,
                    config={"response_mime_type": "application/json", "temperature": 0.3})
                self._track(resp)
                return polish.polish(_parse(resp.text or ""), self.map)
            except Exception as e:      # 429(한도)·일시 오류 등
                last = e
        raise AIUnavailable(f"AI 호출 실패: {type(last).__name__}: {str(last)[:200]}")


    def _track(self, resp) -> None:
        """호출 수와 토큰 수를 하루 단위로 기록한다 (관리자 현황에서 비용을 가늠하는 용도)."""
        try:
            um = resp.usage_metadata
            tin = int(getattr(um, "prompt_token_count", 0) or 0)
            tout = int(getattr(um, "candidates_token_count", 0) or 0) + int(getattr(um, "thoughts_token_count", 0) or 0)
            self.conn.execute(
                """insert into ai_usage (day, model, calls, input_tokens, output_tokens)
                   values ((now() at time zone 'Asia/Seoul')::date, %s, 1, %s, %s)
                   on conflict (day, model) do update set calls = ai_usage.calls + 1,
                     input_tokens = ai_usage.input_tokens + excluded.input_tokens,
                     output_tokens = ai_usage.output_tokens + excluded.output_tokens""", (self.model, tin, tout))
        except Exception:
            pass        # 기록 실패가 분석을 막으면 안 된다


def _parse(text: str) -> dict:
    text = text.strip()
    cands = [text]
    cands += re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    cands += re.findall(r"\{[\s\S]*\}", text)[:1]
    for cand in cands:
        try:
            v = json.loads(cand)
            if isinstance(v, dict):
                return v
        except ValueError:
            pass
    raise ValueError("AI 응답을 JSON으로 읽지 못함")


# ── 프롬프트 ───────────────────────────────────────────────────────────────

def _glossary(notes):
    return f"\n## 이 갤러리 용어 참고 (관리자 입력, 요약에 그대로 옮기지 말고 이해용으로만)\n{notes.strip()[:600]}\n" if notes else ""


def _posts_md(samples, comments, body_len=300):
    out = []
    for p in samples:
        cm = comments.get(p["post_no"], [])
        cm_md = ("\n     댓글 발췌: " + " / ".join(cm[:4])) if cm else ""
        body = (p["body"] or "")[:body_len]
        body_md = f"\n     본문: {body}" if body else ""
        out.append(f"[#{p['post_no']}] {p['title']}  (댓글 {p['comment_count']}, 추천 {p['recommend_count']}"
                   f"{', 개념글' if p['is_best'] else ''}){body_md}{cm_md}")
    return "\n\n".join(out)


def _struct(top_label, n_topics, headline_hint, with_sentiment=True):
    sent = """,
  "sentiment": {"positive": {"summary": "긍정 반응 한두 문장", "evidence": [글번호], "quotes": [{"post": 글번호, "text": "입력에 있는 댓글 원문 그대로"}]},
                "negative": {"summary": "부정 반응 한두 문장", "evidence": [글번호], "quotes": [{"post": 글번호, "text": "입력에 있는 댓글 원문 그대로"}]}}""" if with_sentiment else ""
    sent_rule = """
sentiment 규칙: 반응이 실제로 보이는 쪽만 쓰고, 글·댓글로 뒷받침되지 않으면 그 항목을 통째로 생략하세요. quotes 의 text 는 입력의 '댓글 발췌'에 있는 문장을 한 글자도 바꾸지 말고 그대로 옮기세요(없으면 빈 배열). 근거가 없는 일반론은 쓰지 마세요.""" if with_sentiment else ""
    return f"""{{
  "headline": "{headline_hint}",
  "summary": "3~4문장. 가장 화제가 된 것 → 유저들의 반응 → 전반적인 분위기 순서로 서술",
  "topics": [{{"title": "주제 이름 (15자 이내)", "detail": "그 주제가 무엇이고 유저들이 무엇에 반응했는지 2~3문장", "basis": "post 또는 speculation", "keywords": ["이 주제의 글 제목에 실제로 쓰인 구체적인 단어 2~3개"], "evidence": [글번호]}}]{sent}
}}
topics 는 최대 {n_topics}개이며 {top_label} 순서로 나열하세요. evidence 에는 위 입력의 글번호만 사용하고, 없으면 빈 배열로 두세요.
basis 는 그 주제의 중심이 무엇인지 표시합니다. post = 글이나 댓글에 실제로 적힌 내용이 중심(올라온 공지·소식, 있었던 일, 질문, 공략·정보, 후기, 그리고 불만·감상·항의 같은 유저의 의견 표현 자체도 포함). speculation = 확인되지 않은 원인·의도·앞으로의 일에 대한 짐작·예상·루머가 주제의 중심일 때만(예: '운영이 일부러 그랬을 것이다', '다음 패치에 ~가 나올 것이다'). 불만을 표현하거나 게임을 접겠다고 말하는 것은 speculation 이 아니라 post 입니다. 애매하면 post 로 하세요.
keywords 는 그 주제를 다룬 글을 찾는 데 쓰입니다. '이벤트', '업데이트'처럼 어느 글에나 나올 수 있는 흔한 단어는 피하고 그 주제를 특정하는 단어(고유명사·콘텐츠 이름·사건 이름)를 고르세요.{sent_rule}"""


def daily_issue_prompt(g, day, stats, samples, comments, keywords, rising, floods):
    kw = ", ".join(w for w, _ in keywords[:10]) or "없음"
    rs = ", ".join(f"{w}(오늘 {c}회, 평소 {'10배 이상' if r >= 10 else str(r) + '배'})" for w, c, r in rising) or "없음"
    fl = "\n".join(f"- 같은 제목 {f['count']}건 반복: \"{f['title']}\"" for f in floods[:3]) or "없음"
    return f"""당신은 DC인사이드 게임 갤러리 커뮤니티 동향 분석가입니다.

## 분석 대상
갤러리: {g['name']}  날짜: {day}
게시량 {stats['count']}건 (평소 약 {stats['baseline']:.0f}건)
주제 키워드: {kw}
평소보다 많이 언급된 단어: {rs}
같은 제목 반복(도배) 묶음: {fl}
{_glossary(g.get('notes'))}
## 참여도 상위 글 (글번호 [#번호])
{_posts_md(samples, comments)}

---
아래 JSON 형식으로만 응답하세요.
{_struct('유저 관심이 큰', 3, '그날 가장 화제가 된 일을 한 줄로 (25자 이내)')}

지침:
- {NO_TAXONOMY}
- 욕설이 있어도 불만의 강도를 단정하지 말고, 유저들이 무엇에 반응했는지 중심으로 서술.
- {STYLE}"""


def week_prompt(g, label, total, daily_lines, samples, keywords, floods):
    return _period_prompt(g, "주간", label, total, daily_lines, "", samples, keywords, floods)


def month_prompt(g, label, total, daily_lines, weekly_lines, samples, keywords):
    return _period_prompt(g, "월간", label, total, daily_lines, weekly_lines, samples, keywords, [])


def _period_prompt(g, kind, label, total, daily_lines, weekly_lines, samples, keywords, floods):
    kw = ", ".join(w for w, _ in keywords[:12]) or "없음"
    fl = "\n".join(f"- {f['count']}건 반복: \"{f['title']}\"" for f in floods[:3]) or "없음"
    wk = f"\n주별 요약:\n{weekly_lines}\n" if weekly_lines else ""
    return f"""당신은 DC인사이드 게임 갤러리 커뮤니티 동향 분석가입니다. 이 갤러리 하나만을 위한 {kind} 리포트를 씁니다.
갤러리: {g['name']}  기간: {label}  총 게시글 {total}건
이 리포트의 목적: 이 기간에 유저들이 가장 많이 관심을 가진 것이 무엇인지 순위로 보여주는 것입니다.

일별 요약(이슈였던 날):
{daily_lines or '(평소와 달랐던 날 없음)'}{wk}
주제 키워드: {kw}
반복 게시 묶음: {fl}
{_glossary(g.get('notes'))}
## 참여도 상위 글 (글번호 [#번호])
{_posts_md(samples, {}, body_len=120)}

아래 JSON 형식으로만 응답하세요.
{_struct('유저 관심이 큰 순(가장 화제가 된 것이 1번)', 5, f'이 {kind}에 가장 화제가 된 일을 한 줄로 (25자 이내)', with_sentiment=False)}

지침:
- {NO_TAXONOMY}
- 헤드라인과 요약은 1번 주제를 중심으로, 기간 전체의 흐름(어떤 날 무엇이 커졌고 어떻게 이어졌는지)을 담을 것.
- {STYLE}"""


# ── 결과 정리 ──────────────────────────────────────────────────────────────

def clean_structured(raw: dict, limit: int = 3) -> dict:
    topics_raw = raw.get("topics") if isinstance(raw.get("topics"), list) else raw.get("major_issues")
    topics = []
    for it in (topics_raw if isinstance(topics_raw, list) else [])[:limit]:
        if isinstance(it, dict):
            raw_ev = it.get("evidence") if isinstance(it.get("evidence"), list) else []
            ev = [int(s) for s in (str(x).lstrip("#") for x in raw_ev) if s.isdigit()]
            kws = [str(k) for k in (it.get("keywords") if isinstance(it.get("keywords"), list) else [])][:4]
            basis = str(it.get("basis", "")).strip().lower()
            topics.append({"title": str(it.get("title", "")), "detail": str(it.get("detail", "")), "keywords": kws, "evidence": ev,
                           "basis": basis if basis in ("post", "speculation") else None})
    return {"headline": str(raw.get("headline", "")), "summary": str(raw.get("summary", "")),
            "major_issues": topics, "sentiment_raw": raw.get("sentiment") if isinstance(raw.get("sentiment"), dict) else {}}
