"""AI 결과 후처리: 과장 표현을 중립어로 바꾼다. (프롬프트로 막아도 AI가 어길 때가 있어 코드로 확실히 처리)
관리자 페이지에서 settings 의 'ai.overstatement_map'(JSON {"원문": "대체어"})로 추가·수정할 수 있다."""
import json

from core import db

DEFAULT_MAP = {
    "폭발적으로": "크게", "폭발적인": "큰", "폭발적": "큰", "폭증": "급증", "폭주": "급증", "폭발": "급증",
    "대혼란": "혼란", "아수라장": "혼란", "참사": "문제", "붕괴": "저하", "발칵": "논란", "난리": "논란",
    "극심한": "큰", "극심하게": "크게", "맹비난": "비판", "격분": "불만", "분노가 치솟": "불만이 커지",
}


def load_map(conn) -> dict:
    raw = db.setting(conn, "ai.overstatement_map", cast=str)
    extra = {}
    if raw:
        try:
            v = json.loads(raw)
            extra = {str(k): str(x) for k, x in v.items()} if isinstance(v, dict) else {}
        except ValueError:
            pass
    merged = {**DEFAULT_MAP, **extra}
    return dict(sorted(merged.items(), key=lambda kv: len(kv[0]), reverse=True))   # 긴 표현부터 치환


def polish(obj, mapping: dict):
    if isinstance(obj, str):
        for k, v in mapping.items():
            obj = obj.replace(k, v)
        return obj
    if isinstance(obj, list):
        return [polish(x, mapping) for x in obj]
    if isinstance(obj, dict):
        return {k: polish(v, mapping) for k, v in obj.items()}
    return obj
