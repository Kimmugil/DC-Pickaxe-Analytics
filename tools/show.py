import json, sys, psycopg
sys.path.insert(0, ".")
from core import config
from psycopg.rows import dict_row
sys.stdout.reconfigure(encoding="utf-8")
gid, day = sys.argv[1], sys.argv[2]
with psycopg.connect(config.DATABASE_URL, row_factory=dict_row) as c:
    r = c.execute("select * from reports where period_type='day' and gallery_id=%s and period_start=%s", (gid, day)).fetchone()
    print("헤드라인:", r["headline"], "| 분위기:", r["temperature_tag"], "| 원인:", r["top_cause"], "| 점수", r["issue_score"], "| 글", r["post_count"])
    print("요약:", r["summary"])
    print("카테고리:", {k: v["score"] for k, v in (r["category_scores"] or {}).items()})
    for it in r["major_issues"] or []:
        print(f"\n[이슈] {it['title']} (언급 {it.get('mention_count')}건, {it.get('confidence')})\n   {it['detail']}")
        for p in it.get("ref_posts", []): print(f"   - 근거글: {p['title'][:40]} (댓글 {p['comment_count']})")
    print("\n긍정:", (r["sentiment"] or {}).get("positive"), "\n부정:", (r["sentiment"] or {}).get("negative"))
    e = r["extra"]; print("\n도배 묶음:", e["floods"], "\n급상승 단어:", e["rising"], "\n이벤트 후보:", e["event_candidates"], "\n점수 내역:", e["score_parts"])
    print("\n키워드:", r["keywords"][:8])
    print("\n[실제 인기글 TOP5]")
    for p in r["top_posts"]: print(f"   {p['제목'][:45]} 댓글{p['댓글수']} 추천{p['추천수']}{' [개념글]' if p['개념글'] else ''}")
    print("\n[그날 댓글 많은 글 10개 제목]")
    for x in c.execute("select title, comment_count, is_best from posts where gallery_id=%s and (posted_at at time zone 'Asia/Seoul')::date=%s and not is_notice order by comment_count desc limit 10", (gid, day)).fetchall():
        print(f"   {x['title'][:50]} ({x['comment_count']}){' [개념글]' if x['is_best'] else ''}")
