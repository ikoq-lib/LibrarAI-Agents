"""입고 목록(xlsx/csv) 파서.

납품 목록의 헤더는 업체마다 다르므로 별칭 표로 흡수한다. 필수는 두 가지뿐이다 —
**등록번호와 (ISBN 또는 제목)**. 나머지는 SEOJI 조회로 채운다.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from models import BookInput

# 표준 필드명 → 받아들일 헤더 별칭
ALIASES: dict[str, tuple[str, ...]] = {
    "reg_no": ("등록번호", "등록 번호", "regno", "reg_no", "자료번호", "바코드"),
    "isbn": ("isbn", "isbn13", "ea_isbn", "표준번호"),
    "set_isbn": ("세트isbn", "set_isbn", "세트 isbn"),
    "title": ("서명", "제목", "표제", "본표제", "도서명", "title"),
    "subtitle": ("부서명", "부제", "부표제", "subtitle"),
    "author": ("저자", "저자명", "지은이", "author", "저작자"),
    "publisher": ("출판사", "발행처", "publisher"),
    "pub_place": ("발행지", "출판지", "pub_place"),
    "pub_year": ("발행년", "출판년", "발행연도", "출판연도", "발행일", "pub_year"),
    "room": ("자료실", "대상자료실", "배가자료실", "room", "대상"),
    "price": ("정가", "가격", "price", "단가"),
    "pages": ("면수", "페이지", "쪽수", "pages", "page"),
    "size_cm": ("크기", "판형", "size"),
    "illustration": ("삽화", "삽화사항", "illustration"),
    "series_title": ("총서", "총서명", "시리즈", "series"),
    "series_no": ("총서권호", "권호", "series_no"),
    "vol": ("권차", "권", "vol"),
    "edition": ("판사항", "판", "edition"),
    "isbn_add_code": ("부가기호", "add_code", "ea_add_code"),
    "ctrl_no": ("제어번호", "ctrl_no", "관리번호"),
    "kdc_hint": ("kdc", "청구기호", "분류기호", "분류"),
    "toc": ("목차", "toc"),
    "summary": ("책소개", "요약", "줄거리", "summary"),
    "copies": ("복본수", "부수", "권수", "copies", "수량"),
    "ksh": ("ksh", "주제명번호"),
}

ROOM_CANON = {
    "성인": "성인", "일반": "성인", "종합": "성인", "성인자료실": "성인", "종합자료실": "성인",
    "어린이": "어린이", "아동": "어린이", "어린이자료실": "어린이", "j": "어린이",
    "유아": "유아", "유아자료실": "유아", "영유아": "유아",
}


def _norm_header(text: str) -> str:
    return re.sub(r"[\s_·\-()]", "", str(text or "")).lower()


def _build_index(headers: list[str]) -> dict[str, int]:
    """헤더 행 → {표준 필드명: 열 번호}

    정확 일치를 **전부 먼저** 끝낸 뒤에 부분 일치를 시도한다. 한 번에 처리하면
    앞 필드의 부분 일치가 뒤 필드의 정확 일치 자리를 가로챈다 — 실제로 '출판사'가
    edition의 별칭 '판'에, '권수'가 vol의 별칭 '권'에 걸려 250 판사항이 출판사명으로,
    049 $v 권차가 권수로 채워지는 사고가 났다(2026-09-04).

    그래서 부분 일치에는 두 가지 제약을 둔다 — 이미 다른 필드가 차지한 열은 건드리지
    않고, 한 글자짜리 별칭은 부분 일치에 쓰지 않는다.
    """
    index: dict[str, int] = {}
    normed = [_norm_header(h) for h in headers]

    for field_name, aliases in ALIASES.items():        # 1) 정확 일치
        for alias in aliases:
            target = _norm_header(alias)
            for pos, header in enumerate(normed):
                if header == target and field_name not in index:
                    index[field_name] = pos

    for field_name, aliases in ALIASES.items():        # 2) 부분 일치
        if field_name in index:
            continue
        claimed = set(index.values())
        for alias in aliases:
            target = _norm_header(alias)
            if len(target) < 2:
                continue
            for pos, header in enumerate(normed):
                if pos in claimed or field_name in index:
                    continue
                if target in header:
                    index[field_name] = pos
    return index


def _cell(row: list, index: dict[str, int], name: str) -> str:
    pos = index.get(name)
    if pos is None or pos >= len(row):
        return ""
    value = row[pos]
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def normalize_room(raw: str) -> str:
    key = re.sub(r"\s", "", raw or "").lower()
    return ROOM_CANON.get(key, "성인" if not key else ROOM_CANON.get(key[:3], "성인"))


def normalize_isbn(raw: str) -> str:
    digits = re.sub(r"[^0-9Xx]", "", raw or "")
    return digits.upper()


def normalize_year(raw: str) -> str:
    match = re.search(r"(19|20)\d{2}", raw or "")
    return match.group(0) if match else ""


def _read_rows(path: Path) -> list[list]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        import openpyxl

        book = openpyxl.load_workbook(path, data_only=True)
        sheet = book.worksheets[0]
        return [list(r) for r in sheet.iter_rows(values_only=True)]
    if path.suffix.lower() in (".csv", ".txt"):
        for encoding in ("utf-8-sig", "cp949", "utf-8"):
            try:
                with open(path, encoding=encoding, newline="") as handle:
                    return [row for row in csv.reader(handle)]
            except UnicodeDecodeError:
                continue
        raise ValueError(f"{path} 인코딩을 알 수 없습니다(utf-8/cp949 모두 실패).")
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list) or not data:
            raise ValueError("JSON 입고 목록은 객체 배열이어야 합니다.")
        headers = list(data[0].keys())
        return [headers] + [[row.get(h, "") for h in headers] for row in data]
    raise ValueError(f"지원하지 않는 확장자입니다: {path.suffix}")


def load(path: str | Path) -> list[BookInput]:
    path = Path(path)
    rows = [r for r in _read_rows(path) if any(str(c or "").strip() for c in r)]
    if not rows:
        raise ValueError(f"{path}에 읽을 행이 없습니다.")

    # 헤더 행 찾기 — 별칭이 2개 이상 잡히는 첫 행
    header_pos, index = 0, {}
    for pos, row in enumerate(rows[:10]):
        candidate = _build_index([str(c or "") for c in row])
        if len(candidate) >= 2:
            header_pos, index = pos, candidate
            break
    if not index:
        raise ValueError(
            f"{path}에서 헤더를 찾지 못했습니다. 최소한 '등록번호'와 'ISBN'(또는 '서명') 열이 필요합니다."
        )

    books: list[BookInput] = []
    for seq, row in enumerate(rows[header_pos + 1:], start=1):
        reg_raw = _cell(row, index, "reg_no")
        isbn = normalize_isbn(_cell(row, index, "isbn"))
        title = _cell(row, index, "title")
        if not (reg_raw or isbn or title):
            continue

        reg_nos = [r.strip() for r in re.split(r"[,;/\s]+", reg_raw) if r.strip()]
        copies = _cell(row, index, "copies")
        if copies.isdigit() and int(copies) > len(reg_nos) and reg_nos:
            # 등록번호가 한 개만 오고 복본수만 적힌 목록 — 사서가 나머지를 채워야 한다
            reg_nos = reg_nos + [""] * (int(copies) - len(reg_nos))

        ksh_raw = _cell(row, index, "ksh")
        ksh: dict[str, str] = {}
        for pair in re.split(r"[;|]", ksh_raw):
            if "=" in pair:
                term, _, number = pair.partition("=")
                ksh[term.strip()] = number.strip()

        books.append(
            BookInput(
                seq=seq,
                isbn=isbn,
                set_isbn=normalize_isbn(_cell(row, index, "set_isbn")),
                reg_nos=reg_nos,
                room=normalize_room(_cell(row, index, "room")),
                title=title,
                subtitle=_cell(row, index, "subtitle"),
                author_raw=_cell(row, index, "author"),
                publisher=_cell(row, index, "publisher"),
                pub_place=_cell(row, index, "pub_place"),
                pub_year=normalize_year(_cell(row, index, "pub_year")),
                edition=_cell(row, index, "edition"),
                series_title=_cell(row, index, "series_title"),
                series_no=_cell(row, index, "series_no"),
                vol=_cell(row, index, "vol"),
                pages=_cell(row, index, "pages"),
                illustration=_cell(row, index, "illustration"),
                size_cm=_cell(row, index, "size_cm"),
                price=re.sub(r"[^\d]", "", _cell(row, index, "price")),
                isbn_add_code=re.sub(r"[^\d]", "", _cell(row, index, "isbn_add_code")),
                ctrl_no=re.sub(r"[^\d]", "", _cell(row, index, "ctrl_no")),
                kdc_hint=_cell(row, index, "kdc_hint"),
                toc=_cell(row, index, "toc"),
                summary=_cell(row, index, "summary"),
                ksh=ksh,
                sources={"기본": path.name},
                raw={h: _cell(row, index, h) for h in index},
            )
        )
    if not books:
        raise ValueError(f"{path}에서 도서 행을 하나도 읽지 못했습니다.")
    return books
