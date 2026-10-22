"""환경 설정. .env 파일(로컬) 또는 환경변수(GitHub Actions)에서 읽는다."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_env_file() -> None:
    p = ROOT / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_env_file()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
# 회사망처럼 SSL 검사를 하는 환경에서만 1. 디시 공개 페이지만 읽고 비밀 정보는 보내지 않는다.
DC_INSECURE_SSL = os.environ.get("DC_INSECURE_SSL", "0") == "1"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# settings 표에서 덮어쓸 수 있는 기본값 (관리자 페이지에서 바꾸는 값들)
DEFAULTS = {
    "collector.head_pages": 15,           # 정기 수집 때 훑는 최대 페이지
    "collector.catchup_pages": 40,        # 누락 구간 따라잡기: 한 번에 훑는 페이지
    "collector.initial_pages": 3,         # 새 갤러리 첫 수집 페이지
    "collector.refresh_stage1_h": 12,     # 이 시간이 지난 글의 숫자를 1차 갱신
    "collector.refresh_stage2_h": 36,     # 2차(최종) 갱신
    "collector.refresh_every_h": 6,       # 갤러리별 갱신 작업 최소 간격
    "collector.body_min_comments": 3,     # 이 이상 반응이 있는 글만 본문을 가져옴
    "collector.body_per_run": 60,
    "collector.comments_min": 10,         # 댓글 내용을 가져올 최소 댓글 수
    "collector.comments_per_run": 25,
    "collector.comments_max_pages": 3,
    "collector.cooldown_base_min": 30,    # 차단 감지 시 쉬는 시간(연속될수록 2배, 최대 6시간)
    # ── 분석 ──
    "analyzer.issue_threshold": 3,        # 이 점수 이상이면 '이슈' (평소 대비 이상치 점수라 옛 기준(5)보다 낮음)
    "analyzer.borderline_threshold": 2,   # 이 점수면 '경계' (짧은 AI 요약)
    "analyzer.flood_min": 8,              # 같은 제목이 하루에 이만큼 이상이면 반복글 묶음
    "analyzer.flood_cap": 5,              # 묶음은 점수 계산에서 최대 이만큼만 센다
    "analyzer.min_history_days": 7,       # 기준선을 만들 최소 일수 (모자라면 게시량 급증 점수 생략)
    "analyzer.min_coverage_ratio": 0.7,   # 평소 완성도의 이 비율 미만인 날은 기준선에서 제외
    "ai.model": "gemini-2.5-flash",
    "ai.max_calls_per_run": 40,           # 무료 사용량 보호
    "ai.call_gap_sec": 6,
}
