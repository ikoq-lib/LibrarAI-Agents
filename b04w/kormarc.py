"""KORMARC 레코드 조립 — 전부 코드가 계산한다.

우리 관 목록 정책 3가지가 여기 박혀 있다.
  1) 기본표목 미사용 — 100·110·111을 만들 수 없다. 모든 개인명은 700, 단체명은 710.
  2) 청구기호는 090 — 052를 만들지 않는다. 056에는 KDC 분류기호만.
  3) 책임표시는 245 $d/$e — MARC21식 $c를 쓰지 않는다.

ISBD 구두점은 앞 서브필드의 끝에 붙이고, **어떤 필드도 마침표로 끝나지 않는다.**
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

from config import AUDIENCE, DATA_DIR, ORG_CODE, TAG_ORDER
from fixed_fields import UNKNOWN_PLACE, build_008, control_001, control_005, country_code, leader
from holdings import Holdings
from leejaechul import AuthorMarkError, adjust, author_mark
from models import BookInput, Classification, Field, Record, Result

WON = "\\"   # 정가 앞 원화 기호. 실물 MARC 표기 그대로 역슬래시를 쓴다.

# 마침표 금지가 적용되는 ISBD 기술 필드 (520 요약 같은 산문 주기는 제외)
ISBD_TAGS = ("245", "250", "260", "300", "490", "830", "246", "240")

LANG_NAMES = {
    "eng": "영어", "jpn": "일본어", "fre": "프랑스어", "ger": "독일어", "rus": "러시아어",
    "chi": "중국어", "spa": "스페인어", "ita": "이탈리아어", "swe": "스웨덴어",
    "dan": "덴마크어", "nor": "노르웨이어", "dut": "네덜란드어", "por": "포르투갈어",
}


def _no_trailing_period(value: str) -> str:
    """필드 끝의 마침표를 떼어낸다. 약어 뒤 마침표(p., cm.)는 규칙상 cm만 문제가 된다."""
    return re.sub(r"(?<![A-Za-z])\.\s*$", "", value.rstrip())


def load_publisher_places() -> dict[str, str]:
    path = DATA_DIR / "publisher_places.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("places", {})


def save_publisher_place(publisher: str, place: str) -> None:
    path = DATA_DIR / "publisher_places.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"places": {}}
    data.setdefault("places", {})[publisher] = place
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


@dataclass
class Assembler:
    holdings: Holdings
    entered_place_map: dict[str, str]

    # ── 발행지 ──────────────────────────────────────────────────────────
    def resolve_place(self, book: BookInput, result: Result) -> str:
        if book.pub_place:
            return book.pub_place.strip()
        known = self.entered_place_map.get((book.publisher or "").strip())
        if known:
            result.notes.append(f"발행지 '{known}'는 자관 출판사 소재지 표(publisher_places.json)에서 확인")
            return known
        result.needs_info.append(
            f"발행지 미확인 — 출판사 '{book.publisher or '?'}'의 소재지를 확인해 "
            f"b04w.py --learn-place \"{book.publisher}=발행지\" 로 등록하세요."
        )
        return UNKNOWN_PLACE

    # ── 제어번호 ────────────────────────────────────────────────────────
    def resolve_ctrl_no(self, book: BookInput, result: Result, allocator) -> str:
        if book.ctrl_no:
            return book.ctrl_no
        for holding in self.holdings.by_isbn(book.isbn):
            if holding.ctrl_no:
                result.notes.append(
                    f"기존 소장(ISBN {book.isbn}, 등록번호 {holding.reg_no})의 ctrl_no {holding.ctrl_no} 재사용"
                )
                return str(holding.ctrl_no)
        return str(allocator())

    # ── 저자기호 ────────────────────────────────────────────────────────
    def resolve_author_mark(self, book: BookInput, cls: Classification, result: Result):
        base = cls.author_mark_base or book.author_raw
        mark = author_mark(base, cls.title_proper or book.title)
        if cls.author_mark_note:
            mark.notes.append(cls.author_mark_note)

        # 총서 계승 — 목록의 총서란이 비어 있어도 DB로 확인한다
        series_rows = self.holdings.by_series(book.series_title) if book.series_title else []
        if not series_rows:
            series_rows = self.holdings.by_title_author(book.title, book.author_raw)
        same_work = [
            h for h in series_rows
            if h.isbn and book.isbn and h.isbn == book.isbn
        ]
        if same_work and same_work[0].call_no:
            parts = same_work[0].call_no.split()
            if len(parts) >= 2:
                result.notes.append(
                    f"같은 ISBN의 기존 소장 청구기호 '{same_work[0].call_no}' 계승"
                )
                mark.mark = parts[1]
                mark.derivation += f" → 기존 소장 계승({same_work[0].call_no})"
                if len(parts) >= 3 and not book.vol:
                    book.vol = parts[2]
                    result.notes.append(f"총서 권차 {parts[2]} 계승")
                return mark

        # 충돌 회피 — 같은 분류에 같은 저자기호가 이미 있으면 ±1
        if not self.holdings.available:
            result.notes.append(
                f"장서 DB 미조회({self.holdings.reason}) — 저자기호 충돌 확인을 하지 못했습니다."
            )
            return mark

        for step in (0, 1, -1, 2, -2, 3, -3):
            candidate = mark if step == 0 else None
            if candidate is None:
                try:
                    candidate = adjust(mark, step)
                except AuthorMarkError:
                    continue
            existing = self.holdings.by_call_prefix(cls.kdc, candidate.mark)
            clash = [h for h in existing if not (book.isbn and h.isbn == book.isbn)]
            if not clash:
                if step != 0:
                    result.notes.append(
                        f"저자기호 {mark.mark} 충돌(기존 소장 {len(existing)}건) → {candidate.mark}로 {step:+d} 조정"
                    )
                return candidate
        result.needs_info.append(
            f"저자기호 {mark.mark} 충돌을 ±3 안에서 해소하지 못했습니다. 사서 확인이 필요합니다."
        )
        return mark

    # ── 레코드 ──────────────────────────────────────────────────────────
    def build(self, book: BookInput, cls: Classification, result: Result, allocator) -> Record:
        loc_mark, audience = AUDIENCE.get(book.room, AUDIENCE["성인"])
        place = self.resolve_place(book, result)
        record = Record(leader=leader())

        record.control["001"] = control_001(self.resolve_ctrl_no(book, result, allocator))
        record.control["005"] = control_005()
        record.control["007"] = "ta"
        record.control["008"] = build_008(
            pub_year=book.pub_year,
            country=country_code(place),
            illustration=book.illustration,
            audience=audience,
            has_index=cls.has_index,
            literary_form=cls.literary_form,
        )
        if country_code(place) is None:
            result.needs_info.append("발행국 부호 미확정 — 008/15-17을 공백으로 두었습니다.")

        add = record.fields.append

        # 020 ISBN
        if book.isbn:
            value = f"$a{book.isbn}"
            if book.isbn_add_code:
                value += f" $g{book.isbn_add_code}:"
            if book.price:
                value += f" $c{WON}{book.price}"
            add(Field("020", "__", value))
        else:
            result.needs_info.append("ISBN이 없습니다 — 020을 생성하지 않았습니다.")
        if book.set_isbn:
            add(Field("020", "1_", f"$a{book.set_isbn} (세트)"))   # (세트) 앞 공백 한 칸

        # 040 목록작성기관
        add(Field("040", "__", f"$a {ORG_CODE} $c {ORG_CODE}"))

        # 041 언어부호 — 번역서만, 지시기호 1_
        if cls.is_translation and cls.original_language:
            add(Field("041", "1_", f"$akor $h{cls.original_language}"))

        # 049 소장사항 — $c는 복본기호(2부째부터), 1부면 생략
        reg_nos = [r for r in book.reg_nos if r] or [""]
        parts: list[str] = []
        for order, reg_no in enumerate(reg_nos, start=1):
            if not reg_no:
                result.needs_info.append(f"등록번호 {order}번째가 비어 있습니다.")
                continue
            parts.append(f"$l{reg_no}")
            if book.vol and order == 1:
                parts.append(f"$v{book.vol}")
            if order >= 2:
                parts.append(f"$c{order}")
        if loc_mark:
            parts.append(f"$f{loc_mark}")
        add(Field("049", "0_", " ".join(parts) if parts else "$l[등록번호미정]"))

        # 056 / 090 — 090 $a 는 056 $a 와 반드시 같다
        add(Field("056", "__", f"$a{cls.kdc} $26"))
        add(Field("090", "__", f"$a{cls.kdc} $b{result.author_mark}"))

        # 240 / 245 / 246
        if cls.is_translation and cls.original_title:
            add(Field("240", "00", f"$a{cls.original_title} $l한국어"))

        title = f"$a{cls.title_proper or book.title}"
        if cls.subtitle or book.subtitle:
            title += f" : $b{cls.subtitle or book.subtitle}"
        if book.volume_no:
            title += f". $n{book.volume_no}"
        if book.volume_title:
            title += f", $p{book.volume_title}"
        sor = cls.sor or ([book.author_raw] if book.author_raw else [])
        if sor:
            title += f" / $d{_no_trailing_period(sor[0])}"
            for extra in sor[1:]:
                title += f" ; $e{_no_trailing_period(extra)}"
        else:
            result.needs_info.append("책임표시를 확인하지 못했습니다(245 $d 없음).")
        add(Field("245", "00", title))

        if cls.is_translation and cls.original_title:
            add(Field("246", "19", f"$a{cls.original_title}"))

        # 250 판사항
        if book.edition:
            add(Field("250", "__", f"$a{_no_trailing_period(book.edition)}"))

        # 260 발행사항
        publication = f"$a{place}"
        if book.publisher:
            publication += f" : $b{book.publisher},"
        if book.pub_year:
            publication += f" $c{book.pub_year}"
        add(Field("260", "__", _no_trailing_period(publication)))

        # 300 형태사항 — 쪽 번호가 인쇄돼 있지 않으면 면수를 대괄호로 감싼다
        pages = re.sub(r"[^\d]", "", book.pages or "")
        physical = ""
        if pages:
            physical = f"$a[{pages}] p." if book.unpaged else f"$a{pages} p."
        else:
            result.needs_info.append("면수를 확인하지 못했습니다(300 $a 없음).")
            physical = "$a[면수미확인]"
        if book.illustration:
            physical += f" : $b{book.illustration}"
        if book.size_cm:
            physical += f" ; $c{book.size_cm} cm"
        else:
            result.needs_info.append("크기를 확인하지 못했습니다(300 $c 없음).")
        add(Field("300", "__", physical))

        # 490 / 830 총서
        if book.series_title:
            series = f"$a{book.series_title}"
            if book.series_no or book.vol:
                series += f" ; $v{book.series_no or book.vol}"
            add(Field("490", "10", series))

        # 500 / 504 / 520 / 546 주기
        if cls.is_translation and cls.original_author_native:
            add(Field("500", "__", f"$a원저자명: {cls.original_author_native}"))
        if cls.has_bibliography:
            add(Field("504", "__", "$a참고문헌과 색인 수록" if cls.has_index else "$a참고문헌 수록"))
        if cls.summary:
            add(Field("520", "__", f"$a{cls.summary}"))
        if cls.is_translation:
            language_ko = cls.original_language_ko or LANG_NAMES.get(cls.original_language, "")
            if language_ko:
                add(Field("546", "__", f"$a{language_ko} 원작을 한국어로 번역"))
            else:
                result.needs_info.append("번역서인데 원어를 확인하지 못해 546을 생성하지 못했습니다.")

        # 650 / 651 / 653 — KSH 번호는 사서가 제공한 것만 붙인다
        for heading in cls.subject_headings:
            tag = "651" if heading.get("tag") == "651" else "650"
            term = heading["term"]
            value = f"$a{term}"
            ksh = book.ksh.get(term) or book.ksh.get(re.sub(r"\[.*?\]", "", term).strip())
            if ksh and re.fullmatch(r"KSH\d+", ksh):
                value += f" $0{ksh}"
            add(Field(tag, "_8", value))
        if cls.keywords:
            add(Field("653", "__", " ".join(f"$a{k}" for k in cls.keywords)))
        if not cls.subject_headings and not cls.keywords:
            result.needs_info.append("주제명표목(650/651)도 키워드(653)도 없습니다.")

        # 700 / 710 — 기본표목을 쓰지 않으므로 모든 이름이 여기로 온다
        main_done = False
        for person in cls.contributors:
            name = str(person.get("name") or "").strip()
            if not name:
                continue
            is_corporate = str(person.get("type") or "person") == "corporate"
            value = f"$a{name}"
            if person.get("dates"):
                value += f" $d{person['dates']}"
            if person.get("main") and not main_done:
                value += " $4aut"
                main_done = True
            add(Field("710" if is_corporate else "700", "__" if is_corporate else "1_", value))
        if not main_done:
            result.needs_info.append("주 책임자에게 700 $4aut를 부여하지 못했습니다(사서 확인).")

        # 830 총서 부출표목
        if book.series_title:
            series = f"$a{book.series_title}"
            if book.series_no or book.vol:
                series += f" ; $v{book.series_no or book.vol}"
            add(Field("830", "_0", series))

        # 900 이형 인명 (번역서 원저자 원어 표기)
        if cls.is_translation and cls.original_author_native:
            add(Field("900", "10", f"$a{cls.original_author_native}"))

        # 950 정가
        if book.price:
            add(Field("950", "0_", f"$b{WON}{book.price}"))
        else:
            result.needs_info.append("정가를 확인하지 못했습니다(950 없음).")

        # 마침표 정리 후 tag-order 정렬.
        # ISBD 기술 필드만 대상이다 — 520 요약·500 주기는 산문이라 문장부호를 그대로 둔다.
        for item in record.fields:
            if item.tag in ISBD_TAGS:
                item.value = _no_trailing_period(item.value)
        order = {tag: pos for pos, tag in enumerate(TAG_ORDER)}
        record.fields.sort(key=lambda f: (order.get(f.tag, 999), f.tag))
        return record
