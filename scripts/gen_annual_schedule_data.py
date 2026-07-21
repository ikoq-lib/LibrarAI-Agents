# -*- coding: utf-8 -*-
"""연간 업무 내역.xlsx + 업무_에이전트_매핑.md → annual_schedule_data.js 생성.

사용법: python scripts/gen_annual_schedule_data.py
원본 xlsx는 read_only로 열며 절대 수정하지 않는다. 출력물은 리포 루트의
annual_schedule_data.js (LibrarAI.html이 script 태그로 로드, hwpx_base_template.js와 동일 패턴).
xlsx의 업무명이 매핑 문서에 없으면 경고를 출력한다(생성은 계속).
"""
import json
import re
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "References" / "연간 업무 내역.xlsx"
MAPPING_PATH = ROOT / "References" / "업무_에이전트_매핑.md"
OUT_PATH = ROOT / "annual_schedule_data.js"

DM_WEB_IDS = {
    "DM-01": "dm01-collection-domain",
    "DM-02": "dm02-patron-domain",
    "DM-03": "dm03-reading-culture-domain",
    "DM-04": "dm04-lifelong-learning-domain",
    "DM-05": "dm05-pr-partnership-domain",
}


def read_schedule_rows():
    wb = openpyxl.load_workbook(XLSX_PATH, read_only=True, data_only=True)
    ws = wb["업무일정"]
    rows = list(ws.iter_rows(values_only=True))
    out = []
    for r in rows[1:]:
        if not r[2]:  # 업무명 없는 빈 행 제외
            continue
        out.append({
            "taskType": str(r[0] or "").strip(),
            "taskName": str(r[2]).strip(),
            "cycle": str(r[5] or "").strip(),
            "timing": str(r[6] or "").strip(),
            "detail": str(r[7] or "").strip(),
        })
    wb.close()
    return out


def parse_mapping_table():
    text = MAPPING_PATH.read_text(encoding="utf-8")
    mapping = {}
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5 or cells[0].startswith("---") or cells[0] == "업무종류(원본)":
            continue
        task_name, owner_cell, note = cells[1], cells[2], cells[4]
        owners = []
        for dm in re.findall(r"DM-0[1-5]", owner_cell):
            web_id = DM_WEB_IDS[dm]
            if web_id not in owners:
                owners.append(web_id)
        if "chief-coordinator" in owner_cell:
            owners.append("chief")
        paren = re.search(r"\(([^)]+)\)", owner_cell)
        mapping[task_name] = {
            "owners": owners,
            "leafHint": paren.group(1).strip() if paren else None,
            "note": note or None,
        }
    return mapping


def main():
    rows = read_schedule_rows()
    mapping = parse_mapping_table()

    xlsx_names = {r["taskName"] for r in rows}
    unmapped = sorted(xlsx_names - set(mapping.keys()))
    for name in unmapped:
        print(f"[WARN] unmapped task in xlsx: {name!r} (update References/업무_에이전트_매핑.md)".encode("ascii", "backslashreplace").decode(), file=sys.stderr)
    unused = sorted(set(mapping.keys()) - xlsx_names)
    for name in unused:
        print(f"[NOTE] mapping entry not in xlsx: {name!r}".encode("ascii", "backslashreplace").decode(), file=sys.stderr)

    js = (
        "// 자동 생성 파일 — scripts/gen_annual_schedule_data.py 실행으로 갱신. 직접 수정 금지.\n"
        "// 소스: References/연간 업무 내역.xlsx(업무일정 시트) + References/업무_에이전트_매핑.md\n"
        f"const ANNUAL_SCHEDULE_ROWS = {json.dumps(rows, ensure_ascii=False, indent=1)};\n"
        f"const TASK_AGENT_MAP = {json.dumps(mapping, ensure_ascii=False, indent=1)};\n"
    )
    OUT_PATH.write_text(js, encoding="utf-8")
    print(f"done: {OUT_PATH.name} rows={len(rows)} map={len(mapping)}")


if __name__ == "__main__":
    main()
