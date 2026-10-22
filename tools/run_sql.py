import sys, psycopg
sys.stdout.reconfigure(encoding="utf-8")
url = next(l.split("=",1)[1].strip() for l in open(".env", encoding="utf-8") if l.startswith("DATABASE_URL="))
with psycopg.connect(url, connect_timeout=15) as c:
    c.execute(open(sys.argv[1], encoding="utf-8").read())
    rows = c.execute("""select t.table_name, c.relrowsecurity,
        (select count(*) from information_schema.columns k where k.table_name=t.table_name and k.table_schema='public')
        from information_schema.tables t join pg_class c on c.relname=t.table_name
        join pg_namespace n on n.oid=c.relnamespace and n.nspname='public'
        where t.table_schema='public' order by 1""").fetchall()
    for r in rows: print(f"{r[0]:20} 컬럼 {r[2]:2}개  RLS={'켜짐' if r[1] else '꺼짐'}")
