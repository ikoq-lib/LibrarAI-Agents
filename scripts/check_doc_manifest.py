# -*- coding: utf-8 -*-
"""문서 매니페스트 정합성 검사 (설계 5.7).

`annual_schedule_data.js`의 taskName 집합과 `doc_manifest_data.js`의 taskName 집합을
대조해 한쪽에만 있는 항목을 보고한다. 연간 스케줄이 갱신될 때 매니페스트 누락을 잡는다.

함께 검사하는 것:
  · leaf 가 LibrarAI.html 의 DOMAINS[].agents[].id 에 실재하는가 (설계 5.2 경고)
  · tpl 이 A-01 카탈로그(.claude/agents/a-01-official-document.md)에 있는 번호인가
  · repeat 표기가 규격대로인가

실행: python scripts/check_doc_manifest.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPEAT_RE = re.compile(r"^(monthly|weekly|conditional|manual|(quarterly|yearly):\[\d+(,\s*\d+)*\])$")


def js_array(path: Path, name: str) -> list:
    """`const NAME = [...]` 형태의 배열 리터럴을 JSON으로 읽는다.

    문자열 안팎을 구분하며 훑는다 — 값에 콜론이나 `//`가 들어 있어도 깨지지 않게
    문자열 밖에서만 주석을 지우고 키에 따옴표를 씌운다.
    """
    text = path.read_text(encoding="utf-8")
    start = text.index("[", text.index(f"const {name}"))
    depth, end, pos, in_str = 0, start, start, False
    while pos < len(text):
        ch = text[pos]
        if in_str:
            if ch == "\\":
                pos += 2
                continue
            if ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
        pos += 1

    out, pos, in_str = [], start, False
    body = text[start:end]
    pos = 0
    while pos < len(body):
        ch = body[pos]
        if in_str:
            out.append(ch)
            if ch == "\\":
                out.append(body[pos + 1])
                pos += 2
                continue
            if ch == '"':
                in_str = False
            pos += 1
            continue
        if ch == '"':
            in_str = True
            out.append(ch)
            pos += 1
            continue
        if body.startswith("//", pos):                      # 줄 주석
            pos = body.find("\n", pos)
            if pos < 0:
                break
            continue
        key = re.match(r"([A-Za-z_][\w]*)\s*:", body[pos:])
        if key and (not out or out[-1].strip() in ("{", ",", "")):
            out.append(f'"{key.group(1)}":')
            pos += key.end()
            continue
        out.append(ch)
        pos += 1
    cleaned = re.sub(r",(\s*[}\]])", r"\1", "".join(out))    # 트레일링 콤마
    return json.loads(cleaned)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    schedule = js_array(ROOT / "annual_schedule_data.js", "ANNUAL_SCHEDULE_ROWS")
    manifest = js_array(ROOT / "doc_manifest_data.js", "DOC_MANIFEST_ROWS")

    sched_names = {row["taskName"] for row in schedule}
    man_names = {row["taskName"] for row in manifest}

    problems: list[str] = []
    for name in sorted(sched_names - man_names):
        problems.append(f"매니페스트에 없는 업무: {name}")
    for name in sorted(man_names - sched_names):
        problems.append(f"연간 스케줄에 없는 업무: {name}")

    html = (ROOT / "LibrarAI.html").read_text(encoding="utf-8")
    domains = html[html.index("const DOMAINS"):]
    leaf_ids = set(re.findall(r'id:\s*"([a-z0-9\-]+)"', domains[:9000]))
    catalog = (ROOT / ".claude" / "agents" / "a-01-official-document.md").read_text(encoding="utf-8")
    tpl_ids = set(re.findall(r"`(TPL-\d+|ATT-\d+)`", catalog))

    doc_count = 0
    for row in manifest:
        task = row["taskName"]
        if row.get("leaf") and row["leaf"] not in leaf_ids:
            problems.append(f"{task}: leaf '{row['leaf']}'가 DOMAINS에 없습니다")
        if not REPEAT_RE.match(str(row.get("repeat", ""))):
            problems.append(f"{task}: repeat 표기가 규격 밖입니다 — {row.get('repeat')!r}")
        if row.get("repeat") == "conditional" and not row.get("condition"):
            problems.append(f"{task}: conditional 인데 condition 이 비어 있습니다")
        for doc in row.get("docs", []):
            doc_count += 1
            if doc.get("format") not in ("hwpx", "xlsx", "none"):
                problems.append(f"{task}/{doc.get('title')}: format 이 규격 밖입니다 — {doc.get('format')!r}")
            if doc.get("tpl") and doc["tpl"] not in tpl_ids:
                problems.append(f"{task}/{doc.get('title')}: {doc['tpl']}가 A-01 카탈로그에 없습니다")

    print(f"연간 스케줄 업무 {len(sched_names)}개 / 매니페스트 업무 {len(man_names)}개 "
          f"· 행 {len(manifest)}개 · 문서 {doc_count}건")
    unregistered = sum(1 for row in manifest for d in row.get("docs", []) if not d.get("tpl"))
    print(f"양식 미등록 문서: {unregistered}건")
    if problems:
        print(f"\n지적 {len(problems)}건")
        for item in problems:
            print(f"  · {item}")
        return 1
    print("정합성 이상 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
