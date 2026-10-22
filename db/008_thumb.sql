-- 갤러리 대표 이미지 (디시 갤러리의 og:image 를 줄여서 저장). 쓸 만한 이미지가 없으면 thumb 는 비어 있고 화면은 글자 아바타를 쓴다
alter table galleries
  add column if not exists thumb bytea,
  add column if not exists thumb_checked_at timestamptz;
