-- 3단계: 통합 수집 봇용 변경

alter table galleries
  add column if not exists collect_interval_min integer not null default 60,  -- 갤러리별 수집 주기(분)
  add column if not exists last_refreshed_at    timestamptz,
  add column if not exists notes                text;                         -- 갤러리 용어사전(관리자 입력, AI 참고용)

alter table posts
  add column if not exists is_best            boolean not null default false,  -- 개념글
  add column if not exists is_notice          boolean not null default false,  -- 나중에 공지로 고정된 글(분석 제외)
  add column if not exists source             text    not null default 'live', -- live | migrated
  add column if not exists body_fetched_at    timestamptz,
  add column if not exists comments_fetched_at timestamptz;

-- 이관된 글 표시. 이관 글은 refresh_stage=2, metrics_updated_at 이 비어 있음 (다시 실행해도 안전)
update posts set source = 'migrated' where source = 'live' and refresh_stage = 2 and metrics_updated_at is null;

-- refresh_stage: 0=최초 수집, 1=12h 후 갱신, 2=36h 후 갱신, 3=끝내 확인 못함(삭제 추정)
create index if not exists posts_live_stage_idx on posts (gallery_id, refresh_stage) where source = 'live' and refresh_stage < 2;
create index if not exists posts_enrich_idx on posts (comment_count desc) where source = 'live' and refresh_stage >= 1;

-- 반복글(쿠폰·코드 교환 등) 판별 규칙. 관리자 페이지에서 편집 예정
create table if not exists noise_rules (
  id         serial primary key,
  kind       text not null default 'title_regex' check (kind in ('title_regex')),
  pattern    text not null,
  note       text,
  enabled    boolean not null default true,
  created_at timestamptz not null default now(),
  unique (kind, pattern)
);
insert into noise_rules (pattern, note) values
  ('(쿠폰|코드\s*교환|코드\s*맞교|맞교환|친구\s*초대|친구\s*코드|초대\s*코드|추천인)', '쿠폰·코드 교환·친구초대류')
on conflict do nothing;

-- 과거/누락 구간 따라잡기 진행 위치 (이전 backfill_progress 대체)
drop table if exists backfill_progress;
create table if not exists crawl_cursor (
  gallery_id      text not null references galleries(gallery_id) on delete cascade,
  kind            text not null check (kind in ('catchup','history')),
  last_page       integer not null default 0,
  head_no         bigint,                      -- 마지막 저장 시점의 1페이지 최신 글번호(페이지 밀림 보정용)
  collected_count integer not null default 0,
  done            boolean not null default false,
  updated_at      timestamptz not null default now(),
  primary key (gallery_id, kind)
);

-- 일별 수집 완성도: 그날 글번호 범위 대비 저장된 비율
create table if not exists daily_coverage (
  gallery_id   text not null references galleries(gallery_id) on delete cascade,
  day          date not null,
  saved        integer not null,
  id_min       bigint,
  id_max       bigint,
  completeness numeric,                        -- 0~100
  updated_at   timestamptz not null default now(),
  primary key (gallery_id, day)
);

alter table noise_rules    enable row level security;
alter table crawl_cursor   enable row level security;
alter table daily_coverage enable row level security;
