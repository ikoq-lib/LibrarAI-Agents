"""QA 점검 — b-04-w 에이전트 정의의 Quality Assurance Checklist 중 기계로 확인되는 항목.

여기서 걸린 레코드는 출력물에 남기되 `qa_failed`로 표시하고 사서 검토 대상으로 넘긴다.
사람이 눈으로 확인해야 하는 항목(분류의 타당성, 요약의 사실성)은 여기서 판정하지 않는다.
"""
from __future__ import annotations

import re

from config import FORBIDDEN_TAGS, LDR_VALUE, REQUIRED_TAGS
from models import BookInput, Classification, Record


def check(record: Record, book: BookInput, cls: Classification,
          author_mark: str) -> list[str]:
    problems: list[str] = []
    tags = [f.tag for f in record.fields]

    for tag in FORBIDDEN_TAGS:
        if tag in tags:
            problems.append(f"생성 금지 필드 {tag}가 있습니다.")
    for tag in REQUIRED_TAGS:
        if tag not in tags:
            problems.append(f"필수 필드 {tag}가 없습니다.")

    if record.leader != LDR_VALUE:
        problems.append(f"LDR이 고정값과 다릅니다: {record.leader!r}")
    if len(record.leader) != 24:
        problems.append(f"LDR이 24자가 아닙니다({len(record.leader)}자).")

    ctrl_001 = record.control.get("001", "")
    if len(ctrl_001) != 12 or not ctrl_001.isdigit():
        problems.append(f"001이 12자리 숫자가 아닙니다: {ctrl_001!r}")

    ctrl_008 = record.control.get("008", "")
    if len(ctrl_008) != 40:
        problems.append(f"008이 40자가 아닙니다({len(ctrl_008)}자).")
    else:
        if ctrl_008[29:32] not in ("000", "001"):
            problems.append(f"008/29-31이 000/001이 아닙니다: {ctrl_008[29:32]!r}")
        if ctrl_008[38:40] != "  ":
            problems.append("008/38-39가 공백 2칸이 아닙니다.")
        if ctrl_008[15:18].strip() == "":
            problems.append("008/15-17 발행국 부호가 비어 있습니다(발행지 미확인).")

    field_056 = record.first("056")
    field_090 = record.first("090")
    if field_056 and "$2 6" in field_056.value:
        problems.append("056을 `$2 6`으로 띄어 적었습니다(`$26`이어야 합니다).")
    if field_056 and field_090:
        kdc_056 = field_056.value.split("$a")[1].split("$")[0].strip()
        kdc_090 = field_090.value.split("$a")[1].split("$b")[0].strip()
        if kdc_056 != kdc_090:
            problems.append(f"056 $a({kdc_056})와 090 $a({kdc_090})가 다릅니다.")
    if cls.kdc and not re.fullmatch(r"\d{3}(\.\d+)?", cls.kdc):
        problems.append(f"KDC 분류기호 형식이 이상합니다: {cls.kdc!r}")
    if cls.kdc and len(cls.kdc.split(".")[0]) != 3:
        problems.append(f"KDC 분류기호가 3자리 세목 수준이 아닙니다: {cls.kdc!r}")

    if not author_mark:
        problems.append("저자기호가 비어 있습니다.")

    field_245 = record.first("245")
    if field_245:
        if field_245.ind != "00":
            problems.append(f"245 지시기호가 00이 아닙니다: {field_245.ind!r}")
        if "$c" in field_245.value:
            problems.append("245에 $c를 썼습니다(책임표시는 $d/$e).")
        if "$d" not in field_245.value:
            problems.append("245에 책임표시($d)가 없습니다.")

    field_049 = record.first("049")
    if field_049:
        if "$c1 " in field_049.value or field_049.value.endswith("$c1"):
            problems.append("049에 $c1을 썼습니다(1부 입고면 $c를 생략합니다).")
        if "$l" not in field_049.value:
            problems.append("049에 등록번호($l)가 없습니다.")

    aut_count = sum(1 for f in record.fields if f.tag in ("700", "710") and "$4aut" in f.value)
    if aut_count == 0:
        problems.append("주 책임자에게 $4aut가 부여되지 않았습니다.")
    elif aut_count > 1:
        problems.append(f"$4aut가 {aut_count}번 부여되었습니다(정확히 1번이어야 합니다).")

    if not any(f.tag in ("650", "651", "653") for f in record.fields):
        problems.append("주제명표목(650/651)도 키워드(653)도 없습니다.")
    for field in record.fields:
        if field.tag == "650" and "$0" in field.value:
            ksh = field.value.split("$0")[1].strip()
            if ksh not in book.ksh.values():
                problems.append(f"650 $0에 사서가 제공하지 않은 KSH 번호가 있습니다: {ksh}")

    # 520 요약·505 내용주기는 문장이라 마침표로 끝난다(자관·국중 실물 모두 그렇다).
    # 마침표 금지는 표제·발행·형태 같은 기술 요소에 적용되는 규칙이다.
    for field in record.fields:
        if field.tag in ("505", "520"):
            continue
        if field.value.rstrip().endswith("."):
            problems.append(f"{field.tag} 필드가 마침표로 끝납니다: {field.value[-30:]!r}")

    field_260 = record.first("260")
    if field_260 and "[발행지불명]" in field_260.value:
        problems.append("260 $a 발행지를 확인하지 못했습니다(needs_info).")

    if cls.is_translation:
        field_041 = record.first("041")
        if not field_041:
            problems.append("번역서인데 041이 없습니다.")
        elif field_041.ind != "1_":
            problems.append(f"041 지시기호가 1_이 아닙니다: {field_041.ind!r}")
        if not record.first("546"):
            problems.append("번역서인데 546 언어주기가 없습니다.")

    # 세트 ISBN이 별도 020 행으로 들어가므로 첫 행만 보면 안 된다.
    if book.isbn and record.get("020"):
        if not any(book.isbn in f.value for f in record.get("020")):
            problems.append("020 ISBN이 입고 목록 ISBN과 다릅니다.")

    audience = record.control.get("008", " " * 40)[22]
    loc_mark = ""
    if field_049 and "$f" in field_049.value:
        loc_mark = field_049.value.split("$f")[1].strip()
    expected = {"성인": ("", " "), "어린이": ("J", "b"), "유아": ("유", "a")}.get(book.room, ("", " "))
    if (loc_mark, audience) != expected:
        problems.append(
            f"008/22({audience!r})와 049 $f({loc_mark!r})가 자료실 '{book.room}'과 어긋납니다."
        )

    return problems
