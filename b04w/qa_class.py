"""FN-03.1 분류 타당성 검증 — 하네스가 워커 결과를 대조로 검사한다.

표기 검사(qa.py)를 통과했다고 분류가 맞는 것이 아니다. 2026-09-04 배치 301건은
표기 결함 0건이었으나 288건 중 88건이 오분류였고 그중 51건은 워커가 ok·확신도 high로
보고한 건이었다. 육안이 아니라 본표·관행·배치 내부와의 대조로 검사한다.

  ① 표목 대조      배정 번호의 KDC6 본표 표목과 워커가 적은 표목이 같은가
  ② 대분류 검출    뒤 두 자리가 0인 번호(서가 배열 불가)
  ③ 문학류 교차    원작 언어 ↔ 어문학 강목, 부가기호 ↔ .8, 843 무세분 관행
  ④ 배치 일관성    같은 총서가 다른 번호를 받지 않았는가
  ⑤ 재작업 결과    앞선 분류에서 실제로 바뀌었는가

기계가 판정할 수 없는 것(주제 파악이 옳은가)은 판정하지 않고 사서 확인으로 넘긴다.
"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kdc_table  # noqa: E402

HERE = Path(__file__).resolve().parent
CACHE = HERE / "cache" / "classify"
POLICY = HERE / "data" / "kdc_policy.json"


def load_policy() -> dict:
    """자관 분류 정책 — 미사용 기호와 사서가 인정한 표목."""
    if not POLICY.exists():
        return {"unused_numbers": {}, "accepted_headings": {}}
    return json.loads(POLICY.read_text(encoding="utf-8"))

# 어문학 강목 → 원작 언어
LANG_BY_CLASS = {
    "81": "한국어", "82": "중국어", "83": "일본어", "84": "영어",
    "85": "독일어", "86": "프랑스어", "87": "스페인어", "88": "이탈리아어",
}
LANG_ALIAS = {
    "한국어": "81", "국어": "81", "중국어": "82", "일본어": "83", "영어": "84",
    "미국": "84", "독일어": "85", "프랑스어": "86", "스페인어": "87",
    "이탈리아어": "88", "덴마크어": "859", "스웨덴어": "859", "노르웨이어": "859",
    "네덜란드어": "859",
}


def add_code(isbn: str) -> str:
    """ISBN 부가기호 5자리 — 처리현황에는 없으므로 SEOJI 캐시에서 읽는다."""
    path = HERE / "cache" / "seoji" / f"{(isbn or '').strip()}.json"
    if not path.exists():
        return ""
    try:
        return str(json.loads(path.read_text(encoding="utf-8")).get("EA_ADD_CODE") or "").strip()
    except Exception:
        return ""


def _norm(text: str) -> str:
    return re.sub(r"[\s·,()\[\]]", "", text or "")


def _path_label(kdc_path: str) -> str:
    """kdc_path 마지막 단계의 표목만 뽑는다: '8 문학 → 83 일본문학 → 833.6 현대' → '현대'."""
    last = (kdc_path or "").split("→")[-1].strip()
    return re.sub(r"^[\d.]+\s*", "", last).strip()


def check(row: dict, cls: dict, table: dict, batch: list[dict]) -> list[tuple[str, str]]:
    """(판정, 사유) 목록. 판정은 FAIL / WARN / INFO."""
    out: list[tuple[str, str]] = []
    # 처리현황의 KDC가 최종값이다. 분류 캐시는 워커가 처음 낸 값이라, 사서 확정이나
    # 재작업이 반영되기 전 상태일 수 있다(2026-09-12: 확정값 6건이 옛 번호로 검증됐다).
    kdc = (row.get("KDC") or cls.get("kdc") or "").strip()
    if not kdc:
        return [("FAIL", "분류번호 없음")]

    # 사서가 확정한 번호는 표목까지 본표 표기로 다시 적히므로 대조 대상이 아니다
    if "사서 확정값 적용" in (row.get("메모") or ""):
        return [("INFO", f"사서 확정 분류 {kdc} — 검증 대상 아님")]

    policy = load_policy()
    unused = policy.get("unused_numbers", {})
    if kdc in unused:
        out.append(("FAIL", f"자관 미사용 기호 {kdc} — {unused[kdc]}"))

    # ① 표목 대조
    label, level = kdc_table.lookup(table, kdc)
    said = _path_label(cls.get("kdc_path", ""))
    accepted = (policy.get("accepted_headings", {}).get(kdc) or {}).get("labels", [])
    if said and any(_norm(said) == _norm(x) for x in accepted):
        said = label          # 사서가 타당하다고 인정한 표목은 대조를 통과시킨다
    if level == "none":
        out.append(("FAIL", f"본표에 없는 번호({kdc}) — 조기표 조합이면 근거를 밝힐 것"))
    elif level == "exact" and said:
        if _norm(said) not in _norm(label) and _norm(label) not in _norm(said):
            # 번호가 하네스 권고와 같으면 표목 표현 차이일 뿐 분류 결정은 검증된 것이다.
            # 권고와 다른 번호에서의 표목 불일치만 재작업 사유로 삼는다.
            advised = [x.strip() for x in (row.get("권고KDC") or "").split("또는")]
            if "표목 미확인" in said:
                out.append(("WARN", f"워커가 표목 미확인으로 표시({kdc}, 본표 '{label}')"))
            elif kdc in advised:
                out.append(("WARN", f"표목 인용 미준수: 본표 '{label}' ≠ 워커 '{said}' (번호는 권고와 일치)"))
            else:
                out.append(("FAIL", f"표목 불일치: 본표 '{label}' ≠ 워커 '{said}'"))
    elif level == "parent":
        out.append(("INFO", f"본표 미수록 조합번호 — 상위 {kdc.split('.')[0]} '{label}'"))

    # ② 대분류
    if re.fullmatch(r"\d{3}", kdc):
        if kdc.endswith("00"):
            out.append(("FAIL", f"대분류 {kdc} — 서가 배열 불가"))
        elif kdc.endswith("0"):
            out.append(("WARN", f"강목 {kdc}까지만 부여 — 세목 검토 필요"))

    # ③ 문학류 교차 검증
    # 80x(문학 총류·이론·문장작법)는 어문학 강목이 아니라 언어 대조 대상이 아니다
    if kdc.startswith("8") and not kdc.startswith("80"):
        cls2 = kdc[:2]
        lang_ko = (cls.get("original_language_ko") or "").strip()
        if not cls.get("is_translation") and not lang_ko:
            lang_ko = "한국어"
        expect = LANG_ALIAS.get(lang_ko.replace(" ", ""))
        if expect and not (kdc.startswith(expect) or (expect == "859" and kdc.startswith("859"))):
            out.append(("FAIL", f"문학 언어 불일치: 원작 {lang_ko} → {expect}xx인데 {kdc}"))
        add = add_code(row.get("ISBN", ""))
        # .8=동화는 소설 요목(813·833처럼 X3)의 형식구분일 때만이다. 859.81은 덴마크문학,
        # 859.3은 네덜란드문학처럼 언어 세분이라 대상독자와 무관하다(2026-09-09 오탐 2건).
        if re.fullmatch(r"8\d3\.8\d*", kdc) and add[:1] == "0":
            out.append(("FAIL", f"{kdc}(.8=동화, 아동·유아용)인데 부가기호 첫 자리 0(성인)"))
        if cls2 == "84" and "." in kdc:
            out.append(("FAIL", f"성인 외국소설 무세분 관행 위반({kdc}) — 자관은 843"))
        if kdc == "833.7" and "강담" not in (cls.get("kdc_rationale") or ""):
            out.append(("WARN", "833.7=강담. 일본 현대소설이면 833.6"))

    # ⑤ 재작업 결과
    before, advice = row.get("앞선분류", ""), row.get("권고KDC", "")
    if before and kdc == before:
        out.append(("WARN", f"앞선 분류 {before} 그대로 — 재작업으로 바뀌지 않음"))
    elif advice and kdc not in advice.split(" 또는 "):
        out.append(("INFO", f"권고({advice})와 다른 번호를 선택 — 근거 확인 필요"))
    return out


def consistency(rows: list[dict]) -> list[tuple[str, str]]:
    """④ 배치 내부 일관성 — 같은 총서·같은 서명 계열이 다른 번호를 받았는가."""
    groups: dict[str, list[dict]] = {}
    for row in rows:
        base = re.sub(r"\s*\d+\s*$", "", (row.get("서명") or "").split(":")[0]).strip()
        if len(base) >= 4:
            groups.setdefault(base, []).append(row)
    flags = []
    for base, items in groups.items():
        kdcs = {i.get("KDC", "") for i in items if i.get("KDC")}
        if len(items) > 1 and len(kdcs) > 1:
            for item in items:
                flags.append((item.get("등록번호", ""), f"배치 내 불일치: '{base}' 계열이 {sorted(kdcs)}로 갈림"))
    return flags


def load_rows(out_dir: Path, review_csv: Path) -> list[dict]:
    """처리현황.csv + 앞선 QA 결과(앞선 분류·권고)를 등록번호로 잇는다."""
    status = list(csv.DictReader(open(out_dir / "처리현황.csv", encoding="utf-8-sig")))
    review = {r["등록번호"]: r for r in csv.DictReader(open(review_csv, encoding="utf-8-sig"))}
    for row in status:
        prev = review.get(row.get("등록번호", ""), {})
        row["앞선분류"] = prev.get("현재KDC", "")
        row["권고KDC"] = prev.get("권고KDC", "")
        row["반려유형"] = prev.get("유형", "")
    return status


def main() -> int:
    import argparse

    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="재작업 배치 출력 디렉터리")
    parser.add_argument("--review", required=True, help="앞선 QA 결과 CSV(현재KDC·권고KDC 포함)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    rows = load_rows(out_dir, Path(args.review))
    table = kdc_table.load()
    extra = dict(consistency(rows))

    findings: list[dict] = []
    counts = {"FAIL": 0, "WARN": 0, "INFO": 0, "통과": 0}
    for row in rows:
        isbn = (row.get("ISBN") or "").strip()
        cache_file = CACHE / f"{isbn}.json"
        cls = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
        results = check(row, cls, table, rows)
        if row.get("등록번호") in extra:
            results.append(("WARN", extra[row["등록번호"]]))
        worst = "통과"
        for level in ("FAIL", "WARN", "INFO"):
            if any(r[0] == level for r in results):
                worst = level
                break
        counts[worst] += 1
        findings.append({
            "등록번호": row.get("등록번호", ""),
            "서명": row.get("서명", ""),
            "앞선KDC": row.get("앞선분류", ""),
            "권고KDC": row.get("권고KDC", ""),
            "재분류KDC": row.get("KDC", ""),
            "청구기호": row.get("청구기호", ""),
            "반려유형": row.get("반려유형", ""),
            "워커상태": row.get("상태", ""),
            "확신도": row.get("확신도", ""),
            "판정": worst,
            "지적": " / ".join(f"[{a}] {b}" for a, b in results),
            "분류경로": cls.get("kdc_path", ""),
        })

    path = out_dir / "b04h_fn031_검증.csv"
    with open(path, "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(findings[0].keys()))
        writer.writeheader()
        writer.writerows(findings)
    print(f"검증 {len(findings)}건 → {path}")
    print("  " + " / ".join(f"{k} {v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
