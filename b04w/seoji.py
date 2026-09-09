"""SEOJI(국립중앙도서관 서지정보유통지원시스템) 서지 조회.

우리 관의 **유일한 서지 소스**다. 알라딘 Open API는 2026-07-09 차단, 네이버 책 검색
API는 2026-09-01 종료되어 둘 다 쓰지 않는다.

SEOJI가 주지 않는 값이 있다(발행지, 목차·책소개는 자주 공란). 없는 값을 추정으로
채우지 않고 그대로 비워 둔 뒤 needs_info로 넘긴다.
"""
from __future__ import annotations

import math
import re
import time
import urllib.parse
import urllib.request
import json

from config import SEOJI_URL, env
from models import BookInput

_MIN_INTERVAL = 0.25   # 초 — 연속 호출 간 최소 간격
_last_call = 0.0


def _throttle() -> None:
    global _last_call
    gap = time.time() - _last_call
    if gap < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - gap)
    _last_call = time.time()


def query(**params) -> list[dict]:
    """SEOJI SearchApi.do 를 호출해 docs 배열을 돌려준다."""
    cert_key = env("SEOJI_API_KEY_NL_DIRECT")
    payload = {
        "cert_key": cert_key,
        "result_style": "json",
        "page_no": params.pop("page_no", 1),
        "page_size": params.pop("page_size", 10),
    }
    payload.update({k: v for k, v in params.items() if v})
    url = f"{SEOJI_URL}?{urllib.parse.urlencode(payload)}"

    _throttle()
    with urllib.request.urlopen(url, timeout=20) as response:
        text = response.read().decode("utf-8", "replace")
    if not text.strip():
        raise RuntimeError("SEOJI가 빈 응답을 돌려주었습니다.")
    data = json.loads(text)
    return data.get("docs") or []


def _size_to_cm(book_size: str) -> str:
    """SEOJI BOOK_SIZE('128*188', mm) → 300 $c 세로 크기(cm, 올림)."""
    numbers = [int(n) for n in re.findall(r"\d+", book_size or "")]
    if not numbers:
        return ""
    height_mm = max(numbers)
    if height_mm < 60:          # 이미 cm 로 들어온 값
        return str(height_mm)
    return str(math.ceil(height_mm / 10))


def _pages(page: str) -> str:
    """SEOJI PAGE('229 p.', '1책') → 300 $a 면수 숫자만. 판단 불가면 빈 문자열."""
    text = (page or "").strip()
    match = re.search(r"(\d+)\s*(p|쪽|면)", text, re.I)
    if match:
        return match.group(1)
    if text.isdigit():
        return text
    return ""


def enrich(book: BookInput, *, overwrite: bool = False) -> tuple[BookInput, list[str]]:
    """ISBN(없으면 서명)으로 SEOJI를 조회해 비어 있는 서지 항목을 채운다.

    입고 목록에 이미 있는 값은 건드리지 않는다(overwrite=True면 덮어쓴다).
    """
    notes: list[str] = []
    docs: list[dict] = []
    try:
        if book.isbn:
            docs = query(isbn=book.isbn, page_size=1)
        elif book.title:
            docs = query(title=book.title, page_size=5)
            if book.publisher:
                docs = [d for d in docs if book.publisher in (d.get("PUBLISHER") or "")] or docs
    except Exception as exc:                      # 네트워크·인증 실패는 치명적이지 않다
        notes.append(f"SEOJI 조회 실패: {exc}")
        return book, notes

    if not docs:
        notes.append("SEOJI에 해당 자료가 없습니다(수동 입력 값으로 진행).")
        return book, notes

    doc = docs[0]

    def put(attr: str, value: str, label: str) -> None:
        value = (value or "").strip()
        if not value:
            return
        if getattr(book, attr) and not overwrite:
            return
        setattr(book, attr, value)
        book.sources[label] = "SEOJI"

    put("title", doc.get("TITLE", ""), "표제")
    put("author_raw", doc.get("AUTHOR", ""), "책임표시")
    put("publisher", doc.get("PUBLISHER", ""), "발행처")
    put("pub_year", (doc.get("PUBLISH_PREDATE") or doc.get("REAL_PUBLISH_DATE") or "")[:4], "발행년")
    put("isbn", doc.get("EA_ISBN", ""), "ISBN")
    put("set_isbn", doc.get("SET_ISBN", ""), "세트ISBN")
    put("isbn_add_code", doc.get("EA_ADD_CODE", ""), "부가기호")
    put("edition", doc.get("EDITION_STMT", ""), "판사항")
    put("series_title", doc.get("SERIES_TITLE", ""), "총서")
    put("series_no", doc.get("SERIES_NO", ""), "총서권호")
    put("vol", doc.get("VOL", ""), "권차")
    put("toc", doc.get("BOOK_TB_CNT", ""), "목차")
    put("summary", doc.get("BOOK_INTRODUCTION") or doc.get("BOOK_SUMMARY", ""), "책소개")

    price = re.sub(r"[^\d]", "", doc.get("PRE_PRICE") or doc.get("REAL_PRICE") or "")
    if price:
        put("price", price, "정가")

    pages = _pages(doc.get("PAGE", ""))
    if pages:
        put("pages", pages, "면수")

    size = _size_to_cm(doc.get("BOOK_SIZE", ""))
    if size:
        put("size_cm", size, "크기")

    if (doc.get("EBOOK_YN") or "").upper() == "Y" or (doc.get("FORM") or "") not in ("", "종이책"):
        notes.append(
            f"SEOJI FORM='{doc.get('FORM')}' — 인쇄 단행본이 아닐 수 있습니다(사서 확인)."
        )
    return book, notes
