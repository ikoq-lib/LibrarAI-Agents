#!/usr/bin/env python
"""B-04-W 자료조직 워커 — 배치 CLI.

입고 목록(xlsx/csv)을 받아 도서 1건씩 KDC 분류와 KORMARC 레코드를 만들고,
QA 체크리스트로 자체 검증한 뒤 배치 산출물을 낸다.

  python b04w.py --in 입고목록.xlsx --out-dir outputs/20260904
  python b04w.py --isbn 9788936439996 --reg-no EM100001 --room 성인
  python b04w.py --in 입고목록.xlsx --no-llm        # 분류는 목록의 KDC 열을 그대로 사용
  python b04w.py --validate outputs/.../records.json  # 기존 산출물 QA만 재실행
  python b04w.py --learn-place "창비=파주"           # 출판사 소재지 등록

역할 분담:
  - 코드가 계산 — 리재철 저자기호, LDR·008 자릿수, 지시기호, ISBD 구두점, 청구기호,
    등록번호·제어번호, 별치기호, QA 검증
  - LLM이 판단 — KDC 분류, 주제명표목·키워드, 책임표시 정리, 저자기호 산출 기준 표기
  - 사서가 확인 — needs_info·QA실패로 표시된 건 (이 프로그램은 추정으로 채우지 않는다)
"""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import classify as classify_mod
import ingest
import report
import seoji
from config import DEFAULT_MODEL, load_env
from holdings import Holdings
from kormarc import Assembler, load_publisher_places, save_publisher_place
from leejaechul import AuthorMarkError
from models import BookInput, Field, Record, Result
from qa import check


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="b04w",
        description="B-04-W 자료조직 워커 — 입고 배치를 KDC 분류 + KORMARC 레코드로 변환",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    source = parser.add_argument_group("입력")
    source.add_argument("--in", dest="input", help="입고 목록 파일 (.xlsx / .csv / .json)")
    source.add_argument("--isbn", help="단건 처리 — ISBN")
    source.add_argument("--title", help="단건 처리 — 서명 (ISBN이 없을 때)")
    source.add_argument("--reg-no", help="단건 처리 — 등록번호 (복본은 쉼표로 구분)")
    source.add_argument("--room", default="성인", choices=["성인", "어린이", "유아"],
                        help="대상 자료실 (기본: 성인)")

    output = parser.add_argument_group("출력")
    output.add_argument("--out-dir", help="산출물 디렉터리 (기본: outputs/YYYYMMDD_b04w)")
    output.add_argument("--quiet", action="store_true", help="진행 로그를 줄인다")

    behavior = parser.add_argument_group("동작")
    behavior.add_argument("--model", default=DEFAULT_MODEL, help=f"OpenRouter 모델 (기본: {DEFAULT_MODEL})")
    behavior.add_argument("--no-llm", action="store_true",
                          help="LLM 분류를 건너뛰고 입고 목록의 KDC 열을 그대로 쓴다")
    behavior.add_argument("--no-seoji", action="store_true", help="SEOJI 서지 보강을 건너뛴다")
    behavior.add_argument("--no-db", action="store_true",
                          help="장서 DB 조회를 건너뛴다(저자기호 충돌·총서 계승·자관 관행 확인 불가)")
    behavior.add_argument("--ctrl-start", type=int, default=0,
                          help="제어번호 채번 시작값 (기본: 장서 DB 최대값+1)")
    behavior.add_argument("--limit", type=int, help="앞에서 N건만 처리(시험용)")

    tools = parser.add_argument_group("도구")
    tools.add_argument("--validate", help="기존 records.json 의 QA만 다시 실행한다")
    tools.add_argument("--learn-place", action="append", metavar="출판사=발행지",
                       help="출판사 소재지를 사전에 등록한다(반복 가능)")
    return parser


def log(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, flush=True)


# ── 도서 1건 처리 ────────────────────────────────────────────────────────
def process_one(
    book: BookInput,
    *,
    assembler: Assembler,
    holdings: Holdings,
    allocator,
    args,
) -> Result:
    result = Result(book=book)

    # 1) 서지 보강 (SEOJI)
    if not args.no_seoji:
        book, notes = seoji.enrich(book)
        result.notes.extend(notes)

    if not book.title:
        result.status = "error"
        result.error = "서명을 확인하지 못했습니다(SEOJI 조회 실패 + 목록에도 없음)."
        return result

    # 2) 자관 세목 분포 — 표가 아니라 우리 관 관행으로 분류하기 위한 근거
    practice = ""
    if holdings.available and not args.no_llm:
        loc_mark = {"성인": "", "어린이": "J", "유아": "유"}.get(book.room, "")
        hint = book.kdc_hint or (book.isbn_add_code[2:5] if len(book.isbn_add_code) == 5 else "")
        stats = holdings.subdivision_stats(hint, loc_mark) if hint else []
        if stats:
            practice = "\n".join(
                f"{cls}: {count}건 (별치기호 '{loc_mark or '없음'}')" for cls, count in stats
            )

    # 3) 분류 (LLM 또는 입력값)
    try:
        cls = classify_mod.offline(book) if args.no_llm else classify_mod.classify(
            book, model=args.model, practice=practice
        )
    except Exception as exc:
        result.status = "error"
        result.error = f"분류 실패: {exc}"
        return result

    result.classification = cls
    result.needs_info.extend(cls.needs_info)
    result.notes.extend(cls.notes)
    if not cls.kdc:
        result.status = "needs_info"
        result.needs_info.append("KDC 분류번호를 확정하지 못했습니다.")
        return result
    if cls.confidence == "low":
        result.needs_info.append(
            f"분류 확신도 낮음 — 후보: {', '.join([cls.kdc] + cls.kdc_alternatives)}"
        )

    # 4) 저자기호
    try:
        mark = assembler.resolve_author_mark(book, cls, result)
    except AuthorMarkError as exc:
        result.status = "needs_info"
        result.needs_info.append(str(exc))
        return result
    result.author_mark = mark.mark
    result.author_mark_derivation = mark.derivation
    result.call_no = f"{cls.kdc} {mark.mark}" + (f" {book.vol}" if book.vol else "")

    # 5) 레코드 조립
    try:
        result.record = assembler.build(book, cls, result, allocator)
    except Exception as exc:
        result.status = "error"
        result.error = f"레코드 조립 실패: {exc}"
        return result

    # 6) QA
    result.qa_failures = check(result.record, kdc=cls.kdc, room=book.room)
    if result.qa_failures:
        result.status = "qa_failed"
    elif result.needs_info:
        result.status = "needs_info"
    else:
        result.status = "ok"
    return result


# ── 하위 명령 ────────────────────────────────────────────────────────────
def run_validate(path: str) -> int:
    """기존 records.json 을 다시 QA한다 — 규칙이 바뀌었을 때 과거 산출물 재검증용."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    failed = 0
    for item in data:
        marc = item.get("marc") or {}
        record = Record(
            leader=marc.get("LDR", ""),
            control=marc.get("control", {}),
            fields=[Field(f["tag"], f["ind"], f["value"]) for f in marc.get("fields", [])],
        )
        failures = check(record, kdc=item.get("kdc", ""), room=item.get("room", "성인"))
        label = "ok" if not failures else "FAIL"
        print(f"[{label}] [{item.get('seq')}] {item.get('title')}")
        for failure in failures:
            print(f"        - {failure}")
        failed += bool(failures)
    print(f"\n재검증 {len(data)}건 중 실패 {failed}건")
    return 1 if failed else 0


def run_learn_place(entries: list[str]) -> int:
    for entry in entries:
        if "=" not in entry:
            print(f"형식이 '출판사=발행지'가 아닙니다: {entry}")
            return 1
        publisher, _, place = entry.partition("=")
        save_publisher_place(publisher.strip(), place.strip())
        print(f"등록: {publisher.strip()} → {place.strip()}")
    return 0


# ── main ────────────────────────────────────────────────────────────────
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    load_env()

    if args.learn_place:
        code = run_learn_place(args.learn_place)
        if not (args.input or args.isbn or args.title):
            return code
    if args.validate:
        return run_validate(args.validate)

    # 입력
    if args.input:
        books = ingest.load(args.input)
        batch_name = Path(args.input).stem
    elif args.isbn or args.title:
        books = [
            BookInput(
                seq=1,
                isbn=ingest.normalize_isbn(args.isbn or ""),
                title=args.title or "",
                reg_nos=[r.strip() for r in (args.reg_no or "").split(",") if r.strip()],
                room=args.room,
            )
        ]
        batch_name = "단건"
    else:
        build_parser().print_help()
        return 2

    if args.limit:
        books = books[: args.limit]

    out_dir = Path(args.out_dir or f"outputs/{datetime.now():%Y%m%d}_b04w")
    out_dir.mkdir(parents=True, exist_ok=True)

    holdings = Holdings(enabled=not args.no_db)
    if not holdings.available:
        log(f"⚠ 장서 DB 미연결 — {holdings.reason}", args.quiet)
        log("  저자기호 충돌 확인·총서 권차 계승·자관 관행 교차검증을 건너뜁니다.", args.quiet)

    assembler = Assembler(holdings=holdings, entered_place_map=load_publisher_places())

    # 제어번호 채번기
    next_ctrl = args.ctrl_start or (holdings.max_ctrl_no() + 1 if holdings.available else 1)
    if not args.ctrl_start and not holdings.available:
        log("⚠ 제어번호 채번 기준을 조회하지 못해 1부터 시작합니다(--ctrl-start 권장).", args.quiet)

    counter = {"value": next_ctrl}

    def allocator() -> int:
        value = counter["value"]
        counter["value"] += 1
        return value

    log(f"입고 {len(books)}건 처리 시작 — 산출물: {out_dir}", args.quiet)
    results: list[Result] = []
    for book in books:
        try:
            result = process_one(
                book, assembler=assembler, holdings=holdings, allocator=allocator, args=args
            )
        except Exception as exc:                       # 개별 실패가 배치를 멈추지 않는다
            result = Result(book=book, status="error", error=f"{exc}\n{traceback.format_exc(limit=3)}")
        results.append(result)
        mark = {"ok": "OK  ", "needs_info": "정보부족", "qa_failed": "QA실패", "error": "오류  "}
        detail = result.call_no or (result.error.splitlines()[0] if result.error else "")
        log(f"[{book.seq}/{len(books)}] {book.title[:28]:30} {mark.get(result.status, '')}  {detail}",
            args.quiet)

    # 산출물
    report.write_mrk(results, out_dir / "records.mrk", title=batch_name)
    report.write_json(results, out_dir / "records.json")
    report.write_status_xlsx(results, out_dir / "처리현황.xlsx")

    log("", args.quiet)
    print(report.summary_line(results))
    print(f"출력: {out_dir / 'records.mrk'}")
    print(f"      {out_dir / 'records.json'}")
    print(f"      {out_dir / '처리현황.xlsx'}")

    blocked = [r for r in results if r.status in ("qa_failed", "error")]
    if blocked:
        print(f"\n사서 확인 필요 {len(blocked)}건 — 처리현황.xlsx의 'QA실패'·'확인필요' 열을 보세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
