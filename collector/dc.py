"""디시인사이드 접속·파싱. 이 파일만 디시 페이지 구조를 안다 (구조가 바뀌면 여기만 고친다)."""
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests
import urllib3
from bs4 import BeautifulSoup

from core import config

KST = timezone(timedelta(hours=9))
BASE = "https://gall.dcinside.com"
PREFIX = {"major": "board", "minor": "mgallery/board", "mini": "mini/board"}
GALLTYPE = {"major": "G", "minor": "M", "mini": "MI"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.dcinside.com/",
}
AD_NICKS = {"댓글돌이"}   # 디시가 댓글 사이에 끼워 넣는 광고 줄


class BlockedError(RuntimeError):
    """차단(또는 차단으로 의심되는 비정상 응답). 잡은 즉시 전체 작업을 멈추고 쉰다."""


@dataclass
class ListRow:
    post_no: int
    title: str
    author: str | None
    posted_at: datetime
    time_known: bool
    comment_count: int
    view_count: int
    recommend_count: int
    is_notice: bool
    is_best: bool


def _int(text) -> int:
    m = re.search(r"\d[\d,]*", text or "")
    return int(m.group().replace(",", "")) if m else 0


def _text(tr, selector) -> str:
    el = tr.select_one(selector)
    return el.get_text(strip=True) if el else ""


def _parse_row(tr) -> ListRow | None:
    try:
        no = int(tr.get("data-no") or tr.select_one(".gall_num").get_text(strip=True))
    except (TypeError, ValueError, AttributeError):
        return None
    kind = tr.get("data-type") or ""
    a = tr.select_one(".gall_tit a:not(.reply_numbox)")
    if a is None:
        return None
    d = tr.select_one(".gall_date")
    ts = (d.get("title") or "").strip() if d else ""
    try:
        posted, known = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=KST), True
    except ValueError:   # 정확한 시각이 없으면 날짜만 (예외적)
        try:
            posted, known = datetime.strptime(d.get_text(strip=True), "%y.%m.%d").replace(tzinfo=KST), False
        except (ValueError, AttributeError):
            return None
    w = tr.select_one(".gall_writer")
    return ListRow(
        post_no=no,
        title=a.get_text(" ", strip=True),
        author=(w.get("data-nick") if w else None) or None,
        posted_at=posted,
        time_known=known,
        comment_count=_int(_text(tr, ".reply_num")),
        view_count=_int(_text(tr, ".gall_count")),
        recommend_count=_int(_text(tr, ".gall_recommend")),
        is_notice=(kind == "icon_notice"),
        is_best=kind.startswith("icon_recom"),
    )


def post_url(gtype, gid, no) -> str:
    return f"{BASE}/{PREFIX[gtype]}/view/?id={gid}&no={no}"


class DC:
    def __init__(self, delay=(1.0, 2.0)):
        self.s = requests.Session()
        self.s.headers.update(HEADERS)
        self.verify = not config.DC_INSECURE_SSL
        if not self.verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.delay = delay
        self.n_requests = 0

    def _request(self, method, url, **kw):
        last = None
        for attempt in range(3):
            time.sleep(random.uniform(*self.delay))
            self.n_requests += 1
            try:
                r = self.s.request(method, url, timeout=15, verify=self.verify, **kw)
            except requests.RequestException as e:
                last = e
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code in (403, 429):
                raise BlockedError(f"HTTP {r.status_code}")
            if r.status_code in (200, 404, 410):
                return r
            last = RuntimeError(f"HTTP {r.status_code}")
            time.sleep(5 * (attempt + 1))
        raise RuntimeError(f"요청 실패: {last}")

    # ── 목록 ────────────────────────────────────────────
    def list_page(self, gid, gtype, page=1, recommend=False) -> list[ListRow]:
        params = {"id": gid, "page": page}
        if recommend:
            params["exception_mode"] = "recommend"
        r = self._request("GET", f"{BASE}/{PREFIX[gtype]}/lists/", params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        if soup.select_one("table.gall_list, tbody.listwrap2") is None:
            raise BlockedError("목록 골격 없음 (소프트 차단 또는 잘못된 갤러리 종류)")
        rows = [x for x in (_parse_row(tr) for tr in soup.select("tr.us-post")) if x]
        return rows

    def detect_type(self, gid) -> str | None:
        """갤러리 종류 자동 판별: minor → major → mini 순으로 목록이 정상으로 열리는 곳."""
        for gtype in ("minor", "major", "mini"):
            try:
                if self.list_page(gid, gtype, 1):
                    return gtype
            except BlockedError:
                continue
        return None

    # ── 본문 ────────────────────────────────────────────
    def fetch_body(self, gid, gtype, no) -> str | None:
        r = self._request("GET", f"{BASE}/{PREFIX[gtype]}/view/", params={"id": gid, "no": no})
        if r.status_code != 200:
            return None
        div = BeautifulSoup(r.text, "html.parser").select_one(".write_div")
        return div.get_text(" ", strip=True) if div else None

    # ── 댓글 ────────────────────────────────────────────
    def fetch_comments(self, gid, gtype, no, posted_at, max_pages=3) -> list[dict] | None:
        """댓글 목록. 글이 사라졌으면 None. 광고줄·삭제·빈 댓글은 제외."""
        view = self._request("GET", f"{BASE}/{PREFIX[gtype]}/view/", params={"id": gid, "no": no})
        if view.status_code != 200:
            return None
        tok = BeautifulSoup(view.text, "html.parser").select_one("#e_s_n_o")
        if tok is None:
            return None
        out, seen_raw, total = [], 0, 0
        for page in range(1, max_pages + 1):
            data = {
                "id": gid, "no": no, "cmt_id": gid, "cmt_no": no, "focus_cno": "", "focus_pno": "",
                "e_s_n_o": tok.get("value"), "comment_page": str(page), "sort": "", "prevCnt": "",
                "board_type": "", "_GALLTYPE_": GALLTYPE[gtype],
            }
            r = self._request("POST", f"{BASE}/board/comment/", data=data,
                              headers={"X-Requested-With": "XMLHttpRequest", "Referer": view.url, "Origin": BASE})
            try:
                j = r.json()
            except ValueError:
                raise BlockedError("댓글 응답이 JSON이 아님")
            items = j.get("comments") or []
            total = int(j.get("total_cnt") or 0)
            seen_raw += len(items)
            for c in items:
                parsed = _parse_comment(c, posted_at)
                if parsed:
                    out.append(parsed)
            if not items or seen_raw >= total:
                break
        return out


_CMT_DATE = re.compile(r"(?:(\d{4})\.)?(\d{2})\.(\d{2}) (\d{2}):(\d{2}):(\d{2})")


def _parse_comment(c, posted_at) -> dict | None:
    if (c.get("name") or "") in AD_NICKS or c.get("del_yn") == "Y" or str(c.get("is_delete")) == "1":
        return None
    no = c.get("no") or c.get("c_no")
    text = BeautifulSoup(c.get("memo") or "", "html.parser").get_text(" ", strip=True)
    if not no or not text:
        return None
    when = None
    m = _CMT_DATE.search(c.get("reg_date") or "")
    if m:
        y = int(m.group(1) or posted_at.year)
        try:
            when = datetime(y, int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), tzinfo=KST)
            if not m.group(1) and when < posted_at - timedelta(days=1):   # 연말·연초에 걸친 댓글
                when = when.replace(year=y + 1)
        except ValueError:
            when = None
    return {"comment_no": int(no), "depth": int(c.get("depth") or 0), "author": c.get("name"), "body": text, "posted_at": when}
