"""B-04-W 자료조직 프로그램 — 자료구조."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BookInput:
    """입고 목록 한 행 + SEOJI 조회로 보강한 서지정보.

    사서가 채우는 값(등록번호·자료실)과 API가 채우는 값(표제·출판사…)을 한 곳에 모은다.
    출처는 `sources`에 기록해 처리현황에서 추적할 수 있게 한다.
    """
    seq: int = 0
    isbn: str = ""
    set_isbn: str = ""
    reg_nos: list[str] = field(default_factory=list)   # 등록번호(복본이면 여러 개)
    room: str = "성인"                                  # 성인 / 어린이 / 유아
    title: str = ""
    subtitle: str = ""
    parallel_title: str = ""
    volume_no: str = ""            # 245 $n
    volume_title: str = ""         # 245 $p
    vol: str = ""                  # 049 $v · 장서 DB vol
    author_raw: str = ""
    publisher: str = ""
    pub_place: str = ""
    pub_year: str = ""
    edition: str = ""
    series_title: str = ""
    series_no: str = ""
    pages: str = ""                # "232 p." 또는 "232"
    unpaged: bool | None = None    # 쪽 번호 인쇄 여부(그림책 대괄호 판정). None=미확인
    illustration: str = ""         # "천연색삽화" 등
    size_cm: str = ""
    price: str = ""
    isbn_add_code: str = ""        # 부가기호 5자리
    toc: str = ""
    summary: str = ""
    ctrl_no: str = ""              # 비면 채번
    kdc_hint: str = ""             # 사서가 미리 정한 분류가 있으면
    rework_note: str = ""          # 하네스 재작업 지시(올바른 표목·번호와 사유)
    ksh: dict[str, str] = field(default_factory=dict)  # 주제명 → KSH 번호(사서 제공분만)
    sources: dict[str, str] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class Classification:
    """LLM이 판단하는 부분만 담는다 — 나머지는 전부 코드가 계산한다."""
    kdc: str = ""
    kdc_path: str = ""
    kdc_rationale: str = ""
    kdc_alternatives: list[str] = field(default_factory=list)
    confidence: str = "low"
    title_proper: str = ""
    subtitle: str = ""
    sor: list[str] = field(default_factory=list)          # 245 $d, $e…
    contributors: list[dict] = field(default_factory=list)  # 700/710
    author_mark_base: str = ""
    author_mark_note: str = ""
    is_translation: bool = False
    original_language: str = ""     # jpn / eng / fre …
    original_language_ko: str = ""  # 일본어 / 영어 …
    original_title: str = ""
    original_author_native: str = ""
    literary_form: str = " "        # 008/33 — f 소설 / p 시 / m 수필 / 공백
    subject_headings: list[dict] = field(default_factory=list)  # 650·651
    keywords: list[str] = field(default_factory=list)           # 653
    summary: str = ""
    has_index: bool = False
    has_bibliography: bool = False
    needs_info: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class Field:
    tag: str
    ind: str          # 2자리, 공백은 '_'
    value: str        # "$a... $b..."

    def render(self) -> str:
        # 정렬 기준은 8번째 칸 — outputs/20260902_b04w_kormarc_test/records_normalized.txt 형식
        if self.ind:
            return f"{self.tag} {self.ind} {self.value}".rstrip()
        return f"{self.tag}    {self.value}".rstrip()


@dataclass
class Record:
    leader: str = ""
    control: dict[str, str] = field(default_factory=dict)   # 001·005·007·008
    fields: list[Field] = field(default_factory=list)

    def get(self, tag: str) -> list[Field]:
        return [f for f in self.fields if f.tag == tag]

    def first(self, tag: str) -> Field | None:
        found = self.get(tag)
        return found[0] if found else None


@dataclass
class Result:
    """도서 1건의 처리 결과."""
    book: BookInput
    classification: Classification | None = None
    record: Record | None = None
    call_no: str = ""            # "813.7 정78찌" (장서 DB call_no 형식)
    author_mark: str = ""
    author_mark_derivation: str = ""
    status: str = "ok"           # ok / needs_info / qa_failed / error
    qa_failures: list[str] = field(default_factory=list)
    needs_info: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    error: str = ""
