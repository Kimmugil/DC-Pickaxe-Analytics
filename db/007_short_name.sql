-- 캘린더 칸에 갤러리를 짧게 표시하기 위한 약칭 (관리자 페이지에서 수정)
alter table galleries add column if not exists short_name text;
update galleries set short_name = case gallery_id
  when 'maplerpg' then '메이플' when 'projectcc' then '쿠키런' when 'stoneageia' then '스톤에이지'
  when '7finger' then '세븐나이츠' when 'guhg' then '창세기전' when 'gssc' then '던파' else null end
 where short_name is null;
