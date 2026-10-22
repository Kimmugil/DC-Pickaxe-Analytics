/** 관리자 '설정' 화면에 나오는 값. 기본값은 파이썬(core/config.py)의 DEFAULTS 와 같아야 한다. */
export const SETTING_DEFS: { key: string; label: string; help: string; def: number | string }[] = [
  { key: 'analyzer.issue_threshold', label: '이슈 기준 점수', help: '이 점수 이상이면 이슈로 표시 (평소 대비 점수라 3 정도가 적당)', def: 3 },
  { key: 'analyzer.borderline_threshold', label: '주목 기준 점수', help: '이 점수면 ‘주목’(이슈 직전)으로 표시. AI 요약은 이슈 이상인 날에만 만듭니다', def: 2 },
  { key: 'analyzer.flood_min', label: '도배 묶음 기준(건)', help: '같은 제목이 하루에 이만큼 이상이면 반복 게시 묶음으로 봄', def: 8 },
  { key: 'analyzer.flood_cap', label: '도배 묶음 반영 상한(건)', help: '묶음은 점수 계산에서 최대 이만큼만 셈', def: 5 },
  { key: 'analyzer.min_history_days', label: '기준선 최소 일수', help: '이보다 기록이 적으면 게시량 급증 점수를 계산하지 않음', def: 7 },
  { key: 'ai.model', label: 'AI 모델 이름', help: 'Gemini 모델 이름 (바꾸면 다음 분석부터 적용)', def: 'gemini-2.5-flash' },
  { key: 'ai.price_in', label: '참고용 AI 요금: 입력(달러/100만 토큰)', help: '현황의 비용 추정에만 쓰입니다. 실제 청구액은 아니며, 구글이 요금을 바꾸면 직접 고쳐야 합니다', def: 0.3 },
  { key: 'ai.price_out', label: '참고용 AI 요금: 출력(달러/100만 토큰)', help: '위와 같음 (생각 토큰은 출력으로 계산)', def: 2.5 },
  { key: 'db.limit_mb', label: 'DB 용량 한도(MB)', help: '현황의 사용률 표시용. Supabase Pro 기본 디스크는 8GB(8192)', def: 8192 },
  { key: 'ai.max_calls_per_run', label: 'AI 호출 한도(1회 실행)', help: '비용이 갑자기 늘지 않게 막는 안전장치. 넘으면 그 실행의 나머지는 AI 요약 없이 숫자만 남김', def: 40 },
  { key: 'collector.head_pages', label: '정기 수집 페이지 수', help: '평소 수집 때 최근 글을 훑는 최대 페이지', def: 15 },
  { key: 'collector.refresh_stage1_h', label: '1차 숫자 갱신(시간)', help: '글이 올라온 뒤 이 시간이 지나면 댓글·조회·추천 수를 다시 읽음', def: 12 },
  { key: 'collector.refresh_stage2_h', label: '최종 숫자 갱신(시간)', help: '이 시간이 지나면 최종값으로 확정', def: 36 },
  { key: 'collector.body_min_comments', label: '본문 수집 최소 댓글 수', help: '이 이상 반응이 있는 글만 본문을 가져옴(요청 수 절약)', def: 3 },
  { key: 'collector.comments_min', label: '댓글 내용 수집 최소 댓글 수', help: '이 이상 댓글이 달린 글만 댓글 내용을 가져옴', def: 10 },
  { key: 'collector.cooldown_base_min', label: '차단 시 쉬는 시간(분)', help: '차단이 의심되면 이만큼 쉬고, 연속되면 2배씩 늘어남(최대 6시간)', def: 30 },
]
