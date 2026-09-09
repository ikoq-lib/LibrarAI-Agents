"""KDC6 본표(References/KDC6_for_learning.txt)에서 분류번호 → 표목 표를 만든다.

FN-03.1 ① 표목 대조에 쓴다. 워커가 적은 표목이 본표 표현과 다르면 분류가 틀렸다는
가장 강한 신호다 — 2026-09-04 배치의 오분류 88건 중 53건이 표목 불일치였다.

요목표(앞부분 약 28쪽)는 세목이 없어 오분류의 원인이 되므로 본표만 읽는다.
"""
from __future__ import annotations

import re
from pathlib import Path

BODY_START_PAGE = 29          # 그 앞은 조기표·요목표
_NOTE = re.compile(r"(별법[:：]|→|포함한다|등을|등의|따위|\(|;|[A-Za-z]{2,}|,\s*$)")


def _clean(label: str) -> str:
    label = _NOTE.split(label)[0]
    return re.sub(r"\s+", " ", label).strip(" .·")


def load(path: Path | str = None) -> dict[str, str]:
    path = Path(path or Path(__file__).resolve().parent.parent / "References" / "KDC6_for_learning.txt")
    table: dict[str, str] = {}
    parent = ""
    page = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        marker = re.match(r"-{3,}\s*\[p\.(\d+)\]", line)
        if marker:
            page = int(marker.group(1))
            continue
        if page < BODY_START_PAGE or not line.strip():
            continue
        full = re.match(r"^(\d{3})(?![\d.])\s*(\S.*)$", line)
        if full:
            parent = full.group(1)
            label = _clean(full.group(2))
            if label and parent not in table:
                table[parent] = label
            continue
        sub = re.match(r"^\s*\.(\d+)(?:-\.\d+)?\s*(\S.*)$", line)
        if sub and parent:
            number = f"{parent}.{sub.group(1)}"
            label = _clean(sub.group(2))
            if label and number not in table:
                table[number] = label
    return table


def lookup(table: dict[str, str], number: str) -> tuple[str, str]:
    """(표목, 확인수준) — 정확히 있으면 exact, 상위만 있으면 parent, 없으면 none."""
    number = (number or "").strip()
    if number in table:
        return table[number], "exact"
    if "." in number:
        head = number.split(".")[0]
        # 조기표로 조합한 번호(예: 594.019 표준구분)는 본표에 통째로 실리지 않는다
        if head in table:
            return table[head], "parent"
    return "", "none"


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    t = load()
    print(f"본표 표목 {len(t)}건 적재")
    for n in ("593", "594", "594.5", "005.53", "005.58", "004.73", "694", "696",
              "747", "748", "833", "833.6", "833.7", "833.8", "843", "911", "912", "180", "188"):
        label, level = lookup(t, n)
        print(f"  {n:8s} {level:6s} {label}")
