"""일별 수집 완성도: 그날 저장된 글 수 ÷ 그날 글번호 범위(최소~최대).
삭제된 글도 번호를 차지하므로 100%가 아니어도 정상이다. 같은 갤러리의 평소 수준보다 눈에 띄게 낮은 날이 문제의 날."""
from datetime import date, timedelta


def run_coverage(conn, run, days=14):
    since = date.today() - timedelta(days=days)
    n = conn.execute(
        """insert into daily_coverage (gallery_id, day, saved, id_min, id_max, completeness)
           select gallery_id, d, saved, id_min, id_max,
                  least(100, round(100.0 * saved / nullif(id_max - id_min + 1, 0), 1))
           from (select gallery_id, (posted_at at time zone 'Asia/Seoul')::date d, count(*) saved,
                        min(post_no) id_min, max(post_no) id_max
                 from posts where not is_notice and posted_at >= %s group by 1, 2) t
           on conflict (gallery_id, day) do update set saved = excluded.saved, id_min = excluded.id_min,
             id_max = excluded.id_max, completeness = excluded.completeness, updated_at = now()""",
        (since,)).rowcount
    run.processed += n
    run.note(f"완성도 {n}건 계산")
