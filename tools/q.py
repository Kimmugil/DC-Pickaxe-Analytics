import sys, psycopg
sys.stdout.reconfigure(encoding="utf-8")
url = next(l.split("=",1)[1].strip() for l in open(".env", encoding="utf-8") if l.startswith("DATABASE_URL="))
with psycopg.connect(url) as c:
    for r in c.execute(sys.argv[1]).fetchall(): print(r)
