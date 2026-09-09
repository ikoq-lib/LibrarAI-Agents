"""whole_book_list.xlsx -> Supabase books 테이블 적재용 CSV 정제.

- 원본: References/whole_book_list.xlsx (Sheet2, 73,390행)
- 출력:
  - References/whole_book_list_clean.csv   : supabase/schema.sql의 books 테이블 컬럼 순서에 맞춘 정제 데이터
  - References/whole_book_list_data_issues.csv : 원본 오기로 추정되는 행 목록 (출판년/ISBN) - 임포트에는 포함하되 사서 확인 필요
"""
import csv
import re
import openpyxl

SRC = "References/whole_book_list.xlsx"
OUT_CLEAN = "References/whole_book_list_clean.csv"
OUT_ISSUES = "References/whole_book_list_data_issues.csv"

SCHEMA_COLUMNS = [
    "reg_no", "title", "author", "publisher", "pub_year", "loc_mark",
    "call_no", "vol", "dup_no", "room", "shelf", "material_status",
    "loan_status", "is_blind", "is_biblio_blind", "ctrl_no", "isbn", "price",
]

ISBN_RE = re.compile(r"[0-9]{9,13}[0-9xX]?")


def clean_str(v):
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["Sheet2"]
    rows = ws.iter_rows(values_only=True)
    next(rows)  # 원본 헤더 스킵 (컬럼 순서는 동일)

    issues = []

    with open(OUT_CLEAN, "w", newline="", encoding="utf-8") as f_clean:
        writer = csv.writer(f_clean)
        writer.writerow(SCHEMA_COLUMNS)

        for row in rows:
            (reg_no, title, author, publisher, pub_year, loc_mark, call_no,
             vol, dup_no, room, shelf, material_status, loan_status,
             blind1, blind2, ctrl_no, isbn, price) = row

            reg_no = clean_str(reg_no)
            title = clean_str(title)
            author = clean_str(author)
            publisher = clean_str(publisher)
            loc_mark = clean_str(loc_mark)
            call_no = clean_str(call_no)
            vol = clean_str(vol)
            room = clean_str(room)
            shelf = clean_str(shelf)
            material_status = clean_str(material_status)
            loan_status = clean_str(loan_status)
            isbn = clean_str(isbn)

            is_blind = "t" if clean_str(blind1) == "Y" else "f"
            is_biblio_blind = "t" if clean_str(blind2) == "Y" else "f"

            if pub_year is not None and not (1900 <= pub_year <= 2026):
                issues.append((reg_no, "pub_year", pub_year, ""))

            if isbn and not ISBN_RE.fullmatch(isbn):
                issues.append((reg_no, "isbn", isbn, "표준 10/13자리 형식 아님"))

            writer.writerow([
                reg_no, title, author, publisher, pub_year, loc_mark,
                call_no, vol, dup_no, room, shelf, material_status,
                loan_status, is_blind, is_biblio_blind, ctrl_no, isbn, price,
            ])

    with open(OUT_ISSUES, "w", newline="", encoding="utf-8") as f_issues:
        writer = csv.writer(f_issues)
        writer.writerow(["reg_no", "field", "value", "note"])
        writer.writerows(issues)

    print(f"clean rows written, issues flagged: {len(issues)}")


if __name__ == "__main__":
    main()
