import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import openpyxl


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "References" / "문서 샘플" / "자료개발" / "4. 2026. 제1차 정기구입 도서 심의대상 목록(붙임).xlsx"
OUT_DIR = ROOT / "outputs" / "b01_july_acquisition_20260726"
JSON_OUT = OUT_DIR / "2026년_7월_수서_검토후보_100종.json"
CSV_OUT = OUT_DIR / "2026년_7월_수서_검토후보_100종.csv"

KDC_MAP = {
    "총류": "000",
    "철학": "100",
    "종교": "200",
    "사회과학": "300",
    "자연과학": "400",
    "기술과학": "500",
    "예술": "600",
    "언어": "700",
    "문학": "800",
    "역사": "900",
}

# 자료심의용 후보로서 최소 다양성을 확보한 잠정 쿼터다.
# B-05의 실제 장서 결핍 지수 조회 결과가 아니며, 사서 검토 전에 대체되어야 한다.
QUOTAS = {
    "총류": 10,
    "철학": 10,
    "종교": 7,
    "사회과학": 12,
    "자연과학": 12,
    "기술과학": 12,
    "예술": 8,
    "언어": 7,
    "문학": 12,
    "역사": 10,
}


def isbn_text(value):
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def provisional_timeliness(year):
    # 원자료에 월/일이 없어 2026년 자료도 "3개월 이내"로 확정할 수 없다.
    # 2026년은 보수적 잠정 70점, 2025년은 0점으로 둔다.
    return 70 if year == 2026 else 0


def main():
    workbook = openpyxl.load_workbook(SOURCE, data_only=True, read_only=True)
    sheet = workbook["일반"]
    by_subject = defaultdict(list)
    for row in list(sheet.values)[2:]:
        source_rank, subject, title, author, publisher, pub_year, isbn, quantity, price, note = row
        if not title or subject not in KDC_MAP:
            continue
        isbn = isbn_text(isbn)
        if len(isbn) != 13 or not isbn.isdigit():
            continue
        by_subject[subject].append(
            {
                "source_rank": int(source_rank),
                "subject": subject,
                "title": str(title).strip(),
                "author": str(author or "").strip(),
                "publisher": str(publisher or "").strip(),
                "publication_year": int(pub_year) if pub_year else None,
                "isbn": isbn,
                "quantity": 1,
                "list_price": int(price or 0),
                "source_note": str(note or "").strip(),
            }
        )

    selected = []
    for subject, quota in QUOTAS.items():
        # 최신 연도 우선, 원 심의 순위로 동점 정렬
        candidates = sorted(
            by_subject[subject],
            key=lambda x: (-(x["publication_year"] or 0), x["source_rank"]),
        )
        selected.extend(candidates[:quota])

    # 전체 순위는 시의성 잠정점수, KDC 순환성을 반영해 정렬한다.
    selected.sort(
        key=lambda x: (
            -provisional_timeliness(x["publication_year"]),
            int(KDC_MAP[x["subject"]]),
            x["source_rank"],
        )
    )

    cumulative = 0
    records = []
    for rank, item in enumerate(selected, 1):
        cumulative += item["list_price"]
        timeliness = provisional_timeliness(item["publication_year"])
        demand = 0
        interest = 0
        balance = 50
        total = round(demand * 0.40 + interest * 0.25 + balance * 0.25 + timeliness * 0.10, 1)
        isbn = item["isbn"]
        records.append(
            {
                "rank": rank,
                "candidate_id": f"2026-07-{rank:03d}",
                "isbn": isbn,
                "title": item["title"],
                "author": item["author"],
                "publisher": item["publisher"],
                "publication_date": str(item["publication_year"]),
                "publication_date_precision": "year_only",
                "kdc": KDC_MAP[item["subject"]],
                "kdc_subject": item["subject"],
                "list_price": item["list_price"],
                "quantity": 1,
                "cumulative_amount": cumulative,
                "selection_score_total": total,
                "user_demand_score": demand,
                "social_interest_score": interest,
                "collection_balance_score": balance,
                "publication_timeliness_score": timeliness,
                "desired_book": False,
                "selection_reason_summary": (
                    f"2026년 제1차 정기구입 심의대상 원자료의 ISBN 확인 자료; "
                    f"KDC {KDC_MAP[item['subject']]} 다양성 쿼터 포함. "
                    "실시간 신간·복본·장서결핍 검증 전 검토 후보."
                ),
                "workflow_status": "needs_review",
                "duplicate_check_status": "not_run_b03_unavailable",
                "collection_balance_status": "provisional_b05_unavailable",
                "live_bibliographic_verification": "not_completed",
                "price_verification_status": "source_workbook_only",
                "source_workbook": str(SOURCE.relative_to(ROOT)),
                "source_sheet": "일반",
                "source_row_rank": item["source_rank"],
                "source_url": f"https://search.shopping.naver.com/book/search?query={quote(isbn)}",
                "source_url_status": "generated_lookup_url_not_opened",
                "review_warning": (
                    "원자료가 2026년 제1차 정기구입 심의대상이므로 이미 구입되었을 가능성이 높음. "
                    "B-03 복본 확인 전 선정·예산배분·발주 금지."
                ),
            }
        )

    metadata = {
        "dataset_title": "2026년 7월 수서 검토 후보 100종",
        "dataset_status": "실시간 신간 검증 미완료 / 사서 검토 전 후보",
        "acquisition_type": "정기구입",
        "created_date": "2026-07-26",
        "record_count": len(records),
        "total_list_price": sum(x["list_price"] for x in records),
        "currency": "KRW",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_character": "2026년 제1차 정기구입 자료심의위원회 심의대상 샘플",
        "critical_limitations": [
            "SEOJI 및 네이버 도서 실시간 API 도구가 연결되지 않아 2026년 7월 신간 여부를 검증하지 못함.",
            "B-03 복본 판정을 실행하지 못했으며 모든 후보를 needs_review로 처리함.",
            "B-05 장서 결핍 지수를 조회하지 못해 균형점수는 중립 잠정치 50점임.",
            "이용자 수요 및 베스트셀러 신호를 조회하지 못해 해당 점수는 0점임.",
            "출판일은 원자료의 연도만 사용했으며 월·일은 확정하지 않음.",
            "원자료가 앞선 정기구입 심의대상이므로 이미 소장 중일 가능성이 높아 발주에 사용하면 안 됨.",
        ],
        "score_formula": "수요×0.40 + 관심도×0.25 + 균형×0.25 + 시의성×0.10",
        "provisional_scoring": {
            "user_demand": 0,
            "social_interest": 0,
            "collection_balance": 50,
            "publication_timeliness": "2026년=70, 2025년=0 (월·일 부재로 보수적 잠정치)",
        },
        "kdc_quotas": QUOTAS,
        "records": records,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = list(records[0].keys())
    with CSV_OUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    print(JSON_OUT)
    print(CSV_OUT)
    print(len(records), metadata["total_list_price"])


if __name__ == "__main__":
    main()
