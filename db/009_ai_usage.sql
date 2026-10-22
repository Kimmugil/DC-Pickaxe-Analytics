-- AI(Gemini) 사용량 기록: 하루·모델별 호출 수와 토큰 수. 관리자 현황의 '이번 달 AI 사용량'에 쓴다
create table if not exists ai_usage (
  day           date   not null,
  model         text   not null,
  calls         integer not null default 0,
  input_tokens  bigint  not null default 0,
  output_tokens bigint  not null default 0,
  primary key (day, model)
);
alter table ai_usage enable row level security;
