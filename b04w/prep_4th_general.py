"""2026년 제4차 정기도서 구입 목록 '일반' 시트 → B-04-W 입고 목록 CSV.

구입 목록에는 등록번호와 대상 자료실이 없다. 등록번호는 사서가 이 배치에 배정한
EM197452~EM197752(301개)를 엑셀 순번대로 부여하고, '일반' 시트이므로 자료실은 전부
성인(별치기호 없음)이다.

'주제' 열(총류·철학·…·역사)은 사서가 매긴 KDC 대강이라 분류 힌트로 넘긴다 —
확정값이 아니라 검증 대상이다.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "References" / "2026년 제4차 정기도서 구입 목록.xlsx"

# '주제' 열 → KDC 대강. classify 프롬프트의 본표 발췌 범위를 좁히는 용도다.
SUBJECT_TO_KDC = {
    "총류": "000", "철학": "100", "종교": "200", "사회과학": "300",
    "자연과학": "400", "기술과학": "500", "예술": "600", "언어": "700",
    "문학": "800", "역사": "900",
}

REG_START = 197452
REG_END = 197752


def main(out_path: str) -> int:
    book = openpyxl.load_workbook(SOURCE, data_only=True)
    sheet = book["일반"]
    rows = [
        r for r in sheet.iter_rows(min_row=3, values_only=True)
        if r[0] is not None and r[1] is not None      # 마지막 '계' 행은 주제가 비어 있다
    ]

    expected = REG_END - REG_START + 1
    if len(rows) != expected:
        raise SystemExit(f"도서 {len(rows)}건인데 등록번호는 {expected}개입니다 — 확인이 필요합니다.")

    with open(out_path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "등록번호", "자료실", "순", "주제", "분류", "서명", "저자",
            "출판사", "출판년", "ISBN", "권수", "정가",
        ])
        for offset, row in enumerate(rows):
            seq, subject, title, author, publisher, year, isbn, copies, price, note = row[:10]
            writer.writerow([
                f"EM{REG_START + offset}",
                "성인",
                seq,
                str(subject).strip(),
                (SUBJECT_TO_KDC.get(str(subject).strip(), "") + " " + str(subject).strip()).strip(),
                str(title).strip(),
                str(author or "").strip(),
                str(publisher or "").strip(),
                year,
                str(isbn or "").strip(),
                copies or 1,
                price or "",
            ])
    print(f"{len(rows)}건 → {out_path}")
    print(f"등록번호 EM{REG_START} ~ EM{REG_START + len(rows) - 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "b04w_4th_general_prep.csv"))
