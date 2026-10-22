"""갤러리 대표 이미지: 디시 갤러리 페이지의 og:image 를 가져와 4:3 으로 잘라 줄여서 DB에 저장한다.
쓸 만하지 않은 이미지(디시 기본 로고, 너무 작은 이미지)는 저장하지 않고 '확인함'만 기록한다 → 화면은 글자 아바타를 쓴다."""
import io
import re

from bs4 import BeautifulSoup
from PIL import Image, ImageOps

from core import db
from .dc import BASE, DC, PREFIX

MIN_WIDTH = 300          # 이보다 작으면 늘려서 흐릿해지므로 쓰지 않는다
WHITE_LIMIT = 0.82       # 거의 흰 배경뿐인 이미지(디시 기본 로고)는 쓰지 않는다
OUT_SIZE = (480, 360)


def _usable(im: Image.Image) -> bool:
    if im.width < MIN_WIDTH:
        return False
    small = im.convert("L").resize((64, 64))
    white = sum(1 for px in small.getdata() if px > 240) / (64 * 64)
    return white < WHITE_LIMIT


def fetch_thumb(dc: DC, gid: str, gtype: str) -> bytes | None:
    r = dc._request("GET", f"{BASE}/{PREFIX[gtype]}/lists/", params={"id": gid, "page": 1})
    if r.status_code != 200:
        return None
    meta = BeautifulSoup(r.text, "html.parser").select_one('meta[property="og:image"]')
    url = meta.get("content") if meta else None
    if not url or not re.match(r"https?://", url):
        return None
    img = dc._request("GET", url)
    if img.status_code != 200 or not img.content:
        return None
    try:
        im = Image.open(io.BytesIO(img.content))
        im.load()
    except Exception:
        return None
    if not _usable(im):
        return None
    im = ImageOps.fit(im.convert("RGB"), OUT_SIZE, method=Image.LANCZOS, centering=(0.5, 0.4))
    out = io.BytesIO()
    im.save(out, "JPEG", quality=82, optimize=True)
    return out.getvalue()


def run_thumbs(dc: DC, conn, run, only=None, force=False):
    """이미지가 없고 최근 14일 안에 확인하지 않은 갤러리(또는 --force)만 처리한다."""
    rows = conn.execute(
        """select gallery_id, gallery_type from galleries where is_active
           and (%(force)s or (thumb is null and (thumb_checked_at is null or thumb_checked_at < now() - interval '14 days'))
                or thumb_checked_at < now() - interval '60 days')""", {"force": force}).fetchall()
    if only:
        rows = [r for r in rows if r["gallery_id"] in only]
    got = 0
    for r in rows:
        try:
            data = fetch_thumb(dc, r["gallery_id"], r["gallery_type"])
        except Exception as e:
            if type(e).__name__ == "BlockedError":
                raise
            run.note(f"{r['gallery_id']} 이미지 실패: {type(e).__name__}", partial=True)
            continue
        conn.execute("update galleries set thumb = %s, thumb_checked_at = now() where gallery_id = %s", (data, r["gallery_id"]))
        got += data is not None
        run.note(f"{r['gallery_id']} 이미지 {'저장' if data else '쓸 만한 이미지 없음'}")
    run.processed += len(rows)
