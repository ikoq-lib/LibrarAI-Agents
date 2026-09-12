"""KORMARC 레코드 조립.

여기서는 판단하지 않는다 — classify가 정한 주제·책임표시와 leejaechul이 계산한
저자기호를 받아 **자관 목록 정책대로** 필드를 만든다. 정책은
`.claude/agents/b-04-w-cataloging-worker.md`에 있고, 어긋나면 qa.py가 잡는다.

  · 기본표목 없음 — 100/110/111을 만들지 않는다.
  · 청구기호는 090. 052는 만들지 않는다.
  · 책임표시는 245 $d/$e. $c는 쓰지 않는다.
  · 필드 끝에 마침표를 찍지 않는다.
"""
from __future__ import annotations

import re
from datetime import datetime

from config import AUDIENCE, ORG_CODE, TAG_ORDER
from fixed_fields import (UNKNOWN_PLACE, build_008, control_001, control_005,
                          country_code, hashify, leader)
from models import BookInput, Classification, Field, Record

LANG_KO = {
    "jpn": "일본어", "eng": "영어", "fre": "프랑스어", "ger": "독일어",
    "rus": "러시아어", "chi": "중국어", "spa": "스페인어", "ita": "이탈리아어",
    "swe": "스웨덴어", "dut": "네덜란드어", "por": "포르투갈어", "vie": "베트남어",
}


def _strip_period(text: str) -> str:
    """필드 끝 마침표를 걷어낸다. '2026.' -> '2026', '20 cm.' -> '20 cm'."""
    return re.sub(r"\.\s*$", "", (text or "").strip())


def _pages_value(book: BookInput) -> str:
    """300 $a — 쪽 번호가 인쇄되지 않은 자료는 대괄호로 감싼다."""
    raw = (book.pages or "").strip()
    if not raw:
        return ""
    digits = re.sub(r"[^\d]", "", raw)
    if not digits:
        return _strip_period(raw)
    return f"[{digits}] p." if book.unpaged else f"{digits} p."


def build_020(book: BookInput) -> list[Field]:
    fields: list[Field] = []
    if book.isbn:
        value = f"$a{book.isbn}"
        if book.isbn_add_code:
            value += f" $g{book.isbn_add_code}"
        if book.price:
            # 정가 앞은 ISBD 구두점 ' : ' — 앞 서브필드 끝에 붙인다
            value += f": $c\\{int(book.price)}"
        fields.append(Field("020", "__", _strip_period(value)))
    if book.set_isbn and book.set_isbn != book.isbn:
        fields.append(Field("020", "1_", f"$a{book.set_isbn} (세트)"))
    return fields


def build_245(cls: Classification) -> Field:
    value = f"$a{_strip_period(cls.title_proper)}"
    if cls.subtitle:
        value += f" : $b{_strip_period(cls.subtitle)}"
    sor = [s for s in cls.sor if s.strip()]
    if sor:
        value += f" / $d{_strip_period(sor[0])}"
        for extra in sor[1:]:
            value += f" ; $e{_strip_period(extra)}"
    return Field("245", "00", value)


def build_260(book: BookInput) -> Field:
    place = book.pub_place.strip() or UNKNOWN_PLACE
    value = f"$a{place} : $b{_strip_period(book.publisher)}, $c{_strip_period(book.pub_year)}"
    return Field("260", "__", value)


def build_300(book: BookInput) -> Field:
    pages = _pages_value(book)
    value = f"$a{pages}" if pages else "$a1책"
    illus = _strip_period(book.illustration)
    if illus:
        value += f" : $b{illus}"
    if book.size_cm:
        value += f" ; $c{book.size_cm} cm"
    return Field("300", "__", value)


def build(book: BookInput, cls: Classification, author_mark: str, ctrl_no: str,
          *, now: datetime | None = None) -> Record:
    now = now or datetime.now()
    loc_mark, audience = AUDIENCE.get(book.room, ("", " "))
    place_code = country_code(book.pub_place)

    record = Record(leader=leader())
    record.control["001"] = control_001(ctrl_no)
    record.control["005"] = control_005(now)
    record.control["007"] = "ta"
    record.control["008"] = build_008(
        pub_year=book.pub_year,
        country=place_code,
        illustration=book.illustration,
        audience=audience,
        has_index=cls.has_index,
        literary_form=cls.literary_form,
        entered=now,
    )

    fields: list[Field] = []
    fields += build_020(book)
    fields.append(Field("040", "__", f"$a {ORG_CODE} $c {ORG_CODE}"))

    if cls.is_translation and cls.original_language:
        fields.append(Field("041", "1_", f"$akor $h{cls.original_language}"))

    holding = " ".join(f"$l{r}" for r in book.reg_nos if r)
    if book.vol:
        holding += f" $v{book.vol}"
    copies = len([r for r in book.reg_nos if r])
    if copies > 1:
        holding += f" $c{copies}"          # 복본기호 — 1부만 입고되면 $c 자체를 쓰지 않는다
    if loc_mark:
        holding += f" $f{loc_mark}"
    fields.append(Field("049", "0_", holding.strip()))

    fields.append(Field("056", "__", f"$a{cls.kdc} $26"))
    fields.append(Field("090", "__", f"$a{cls.kdc} $b{author_mark}"))

    if cls.is_translation and cls.original_title:
        fields.append(Field("240", "00", f"$a{cls.original_title} $l한국어"))

    fields.append(build_245(cls))

    if cls.is_translation and cls.original_title:
        fields.append(Field("246", "19", f"$a{cls.original_title}"))
    if book.edition:
        fields.append(Field("250", "__", f"$a{_strip_period(book.edition)}"))

    fields.append(build_260(book))
    fields.append(build_300(book))

    if book.series_title:
        series = f"$a{_strip_period(book.series_title)}"
        if book.series_no:
            series += f" ; $v{book.series_no}"
        fields.append(Field("490", "10", series))

    if cls.is_translation and cls.original_author_native:
        fields.append(Field("500", "__", f"$a원저자명: {_strip_period(cls.original_author_native)}"))
    if cls.has_bibliography:
        note = "참고문헌과 색인 수록" if cls.has_index else "참고문헌 수록"
        fields.append(Field("504", "__", f"$a{note}"))
    if cls.summary:
        fields.append(Field("520", "__", f"$a{cls.summary.strip()}"))
    if cls.is_translation:
        lang = cls.original_language_ko or LANG_KO.get(cls.original_language, "")
        if lang:
            fields.append(Field("546", "__", f"$a{lang} 원작을 한국어로 번역"))

    for heading in cls.subject_headings:
        tag = heading.get("tag") or "650"
        term = _strip_period(heading.get("term", ""))
        # 한자가 아예 없는 표목은 대괄호를 생략한다 — '유토피아[--]'처럼 채움표만 남은
        # 대괄호는 표기 규칙 위반이다(대괄호는 대응 한자가 있을 때만 쓴다).
        term = re.sub(r"\[-+\]$", "", term).strip()
        if not term:
            continue
        value = f"$a{term}"
        ksh = book.ksh.get(heading.get("term", "").split("[")[0].strip())
        if ksh:
            value += f" $0{ksh}"
        fields.append(Field(tag if tag in ("650", "651") else "650", "_8", value))

    if cls.keywords:
        fields.append(Field("653", "__", " ".join(f"$a{_strip_period(k)}" for k in cls.keywords)))

    # $4aut(주 책임자)은 정확히 1회다. 공저를 둘 다 main 으로 표시해 온 경우
    # 첫 사람만 주 책임자로 둔다(2026-09-12 실측: 「처음 만나는 지경학」 2회 부여).
    main_seen = False
    for person in cls.contributors:
        name = _strip_period(str(person.get("name") or ""))
        if not name:
            continue
        is_main = bool(person.get("main")) and not main_seen
        if is_main:
            main_seen = True
        if (person.get("type") or "person") == "corporate":
            value = f"$a{name}"
            if is_main:
                value += " $4aut"
            fields.append(Field("710", "__", value))
            continue
        value = f"$a{name}"
        if person.get("dates"):
            value += f" $d{person['dates']}"
        if is_main:
            value += " $4aut"
        fields.append(Field("700", "1_", value))

    if book.series_title:
        series = f"$a{_strip_period(book.series_title)}"
        if book.series_no:
            series += f" ; $v{book.series_no}"
        fields.append(Field("830", "_0", series))

    if cls.is_translation and cls.original_author_native:
        fields.append(Field("900", "10", f"$a{_strip_period(cls.original_author_native)}"))

    if book.price:
        fields.append(Field("950", "0_", f"$b\\{int(book.price)}"))

    # 태그 순서로만 정렬한다(파이썬 정렬은 안정적이라 같은 태그 안에서는 만든 순서가 남는다).
    # 지시기호를 정렬 키에 넣으면 `020 1_`(세트 ISBN)이 `020 __`(본 ISBN)보다 앞서서
    # 레코드의 첫 020이 세트 번호가 된다.
    order = {tag: pos for pos, tag in enumerate(TAG_ORDER)}
    record.fields = sorted(fields, key=lambda f: order.get(f.tag, 99))
    return record


def render(record: Record) -> str:
    """레코드를 텍스트로 출력한다. LDR·008만 공백을 '#'로 치환한다."""
    lines = [f"LDR    {hashify(record.leader)}"]
    for tag in ("001", "005", "007", "008"):
        value = record.control.get(tag)
        if not value:
            continue
        lines.append(f"{tag}    {hashify(value) if tag == '008' else value}")
    lines += [f.render() for f in record.fields]
    return "\n".join(lines)
