-- 공식 이벤트(점검·업데이트·방송 등): 자동 후보 + 관리자 원클릭 확인.
-- 이 기능을 빼려면: analyzer/events.py 삭제, daily.py 의 'events' 호출 한 줄 삭제, 아래 표 drop.
create table if not exists events (
  id              bigserial primary key,
  gallery_id      text not null references galleries(gallery_id) on delete cascade,
  event_date      date not null,
  kind            text not null default 'other' check (kind in ('maintenance','update','event','broadcast','other')),
  title           text not null,
  status          text not null default 'candidate' check (status in ('candidate','confirmed','rejected')),
  source_post_no  bigint,
  created_at      timestamptz not null default now(),
  unique (gallery_id, event_date, title)
);
create index if not exists events_gallery_date_idx on events (gallery_id, event_date);
alter table events enable row level security;
