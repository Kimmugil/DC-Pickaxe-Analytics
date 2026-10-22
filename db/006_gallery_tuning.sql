-- 갤러리별 이슈 판정 조절 (관리자 페이지에서 수정). 자동 조절(최근 28일 이슈율 기준)은 코드에서 추가로 적용됨
alter table galleries
  add column if not exists issue_threshold_adjust smallint not null default 0,   -- 기준 점수에 더할 값(-2~+3)
  add column if not exists min_issue_posts        integer  not null default 0;   -- 하루 유효 게시량이 이보다 적으면 이슈로 보지 않음
