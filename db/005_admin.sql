-- 5단계: 관리자 페이지용

-- AI 결과 검토(맞음/틀림). target 예: 'report', 'issue:0'(이슈 순번), 'flood:0'(도배 묶음 순번)
create table if not exists report_feedback (
  id         bigserial primary key,
  report_id  bigint not null references reports(id) on delete cascade,
  target     text not null default 'report',
  verdict    text not null check (verdict in ('ok', 'weak', 'wrong')),
  note       text,
  created_at timestamptz not null default now(),
  unique (report_id, target)
);

-- 관리자 로그인 시도 기록 (무차별 대입 방지). IP 는 해시로만 저장
create table if not exists admin_login_attempts (
  id         bigserial primary key,
  ip_hash    text not null,
  success    boolean not null,
  created_at timestamptz not null default now()
);
create index if not exists admin_login_attempts_idx on admin_login_attempts (ip_hash, created_at desc);

alter table report_feedback        enable row level security;
alter table admin_login_attempts   enable row level security;
