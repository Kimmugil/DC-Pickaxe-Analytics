"""DB 연결, 설정값 읽기/쓰기, 실행 기록(job_runs)."""
import psycopg
from psycopg.rows import dict_row

from core import config


def connect():
    if not config.DATABASE_URL:
        raise RuntimeError("DATABASE_URL 이 설정되지 않았습니다 (.env 확인)")
    return psycopg.connect(config.DATABASE_URL, row_factory=dict_row, autocommit=True, connect_timeout=20)


def setting(conn, key, cast=None):
    """settings 표 값 → 없으면 코드의 기본값."""
    default = config.DEFAULTS.get(key)
    r = conn.execute("select value from settings where key = %s", (key,)).fetchone()
    if r is None or r["value"] in (None, ""):
        return default
    try:
        return (cast or type(default) or str)(r["value"])
    except (TypeError, ValueError):
        return default


def set_setting(conn, key, value):
    conn.execute(
        "insert into settings(key, value) values (%s, %s) "
        "on conflict (key) do update set value = excluded.value, updated_at = now()",
        (key, None if value is None else str(value)),
    )


class JobRun:
    """with JobRun(conn, 'scrape') as run: ...  → job_runs 에 시작/결과를 남긴다."""

    def __init__(self, conn, job, gallery_id=None):
        self.conn, self.job, self.gallery_id = conn, job, gallery_id
        self.processed, self.partial, self._notes = 0, False, []

    def __enter__(self):
        r = self.conn.execute(
            "insert into job_runs(job, gallery_id) values (%s, %s) returning id", (self.job, self.gallery_id)
        ).fetchone()
        self.id = r["id"]
        return self

    def note(self, msg, partial=False):
        self._notes.append(str(msg))
        self.partial = self.partial or partial

    def __exit__(self, et, ev, tb):
        if et:
            status, msg = "failed", f"{et.__name__}: {ev}"
        else:
            status, msg = ("partial" if self.partial else "success"), "; ".join(self._notes)
        self.conn.execute(
            "update job_runs set finished_at = now(), status = %s, processed = %s, message = %s where id = %s",
            (status, self.processed, msg[:1000] or None, self.id),
        )
        return False
