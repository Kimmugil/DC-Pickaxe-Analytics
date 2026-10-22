-- DC-Pickaxe v2 초기 스키마. 시간은 모두 timestamptz(UTC 저장, 화면에서 KST 변환).

create table galleries (
  gallery_id        text primary key,
  name              text not null,
  gallery_type      text not null default 'minor' check (gallery_type in ('major','minor','mini')),
  is_active         boolean not null default true,
  created_at        timestamptz not null default now(),
  last_collected_at timestamptz,
  last_result       text
);

create table posts (
  gallery_id        text not null references galleries(gallery_id) on delete cascade,
  post_no           bigint not null,
  title             text not null,
  body              text,
  body_purged       boolean not null default false,   -- 90일 지나 본문을 비웠는지
  author            text,
  posted_at         timestamptz not null,
  posted_time_known boolean not null default true,    -- false면 날짜만 알고 시각은 모름
  url               text,
  comment_count     integer not null default 0,
  view_count        integer not null default 0,
  recommend_count   integer not null default 0,
  refresh_stage     smallint not null default 0,      -- 0=최초, 1=24h 갱신, 2=48h 갱신
  metrics_updated_at timestamptz,
  is_repetitive     boolean not null default false,   -- 쿠폰/코드 교환 등 반복글
  collected_at      timestamptz not null default now(),
  primary key (gallery_id, post_no)
);
create index posts_gallery_time_idx on posts (gallery_id, posted_at desc);
create index posts_refresh_idx on posts (refresh_stage, posted_at) where refresh_stage < 2;

create table comments (
  gallery_id   text not null,
  post_no      bigint not null,
  comment_no   bigint not null,
  depth        smallint not null default 0,           -- 0=댓글, 1=대댓글
  author       text,
  body         text,
  posted_at    timestamptz,
  collected_at timestamptz not null default now(),
  primary key (gallery_id, post_no, comment_no),
  foreign key (gallery_id, post_no) references posts(gallery_id, post_no) on delete cascade
);

create table reports (
  id               bigserial primary key,
  period_type      text not null check (period_type in ('day','week','month')),
  period_start     date not null,
  period_end       date not null,
  gallery_id       text references galleries(gallery_id) on delete cascade,  -- null이면 전체 종합
  post_count       integer,
  avg_7d           numeric,
  avg_same_weekday numeric,
  momentum_avg     numeric,
  issue_score      smallint,
  has_issue        boolean not null default false,
  is_borderline    boolean not null default false,
  headline         text,
  summary          text,
  temperature_tag  text,
  top_cause        text,
  category_scores  jsonb,
  major_issues     jsonb,
  sentiment        jsonb,
  top_posts        jsonb,
  keywords         jsonb,
  daily_counts     jsonb,
  run_id           text,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create unique index reports_unique_idx on reports (period_type, period_start, coalesce(gallery_id, ''));
create index reports_gallery_idx on reports (gallery_id, period_type, period_start desc);

create table keyword_daily (
  gallery_id text not null references galleries(gallery_id) on delete cascade,
  day        date not null,
  keyword    text not null,
  count      integer not null,
  primary key (gallery_id, day, keyword)
);

create table job_runs (
  id          bigserial primary key,
  job         text not null,                          -- scrape / refresh / daily / weekly / monthly / backup
  gallery_id  text,
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  status      text not null default 'running' check (status in ('running','success','partial','failed')),
  processed   integer,
  message     text
);
create index job_runs_idx on job_runs (job, started_at desc);

create table settings (
  key        text primary key,
  value      text,
  updated_at timestamptz not null default now()
);

create table backfill_progress (
  gallery_id      text primary key references galleries(gallery_id) on delete cascade,
  last_page       integer not null default 0,
  collected_count integer not null default 0,
  done            boolean not null default false,
  updated_at      timestamptz not null default now()
);

-- 모든 표에 접근 제한(RLS) 활성화: 서버(DB 비밀번호)로만 접근
alter table galleries         enable row level security;
alter table posts             enable row level security;
alter table comments          enable row level security;
alter table reports           enable row level security;
alter table keyword_daily     enable row level security;
alter table job_runs          enable row level security;
alter table settings          enable row level security;
alter table backfill_progress enable row level security;
