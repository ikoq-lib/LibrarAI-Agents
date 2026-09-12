"""B-04-W 배치 실행기 — 입고 목록 한 건씩을 KORMARC 레코드로 만든다.

단계는 여섯이고, 각 단계의 결과는 `b04w/cache/`에 ISBN 단위로 저장한다. 중간에
끊기거나 다시 돌려도 이미 조회한 건은 다시 부르지 않는다(외부 API 호출이 배치당
수백 건이라 재실행 비용이 그대로 돈이다).

  1) SEOJI      — 표제·책임표시·면수·판형·부가기호·정가 (직렬, 0.25초 간격)
  2) 웹검색     — 목차·책소개·번역 정보 (도서 단위, 병렬)
  3) 발행지     — 260 $a·008/15-17 (출판사 단위, 병렬 — 도서보다 수가 적다)
  4) 장서 DB    — ctrl_no 재사용·복본 판정·같은 저자 분류 선례 (병렬)
  5) 분류       — KDC·주제명·책임표시 정리 (병렬, LLM)
  6) 조립·QA    — 저자기호 계산, 레코드 조립, 점검 (직렬, 결정론적)

사용:
    python run_batch.py --input ../.artifacts/b04w_4th_general_prep.csv \
        --out ../outputs/20260904_b04w_4th_general [--limit 5] [--workers 8]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import classify as classify_mod          # noqa: E402
import ingest                            # noqa: E402
import leejaechul                        # noqa: E402
import marc                              # noqa: E402
import places                            # noqa: E402
import qa                                # noqa: E402
import seoji                             # noqa: E402
import webenrich                         # noqa: E402
from config import DEFAULT_MODEL, load_env  # noqa: E402
from holdings import Holdings            # noqa: E402
from models import BookInput, Classification, Result  # noqa: E402

CACHE = HERE / "cache"
_print_lock = threading.Lock()
_cost_lock = threading.Lock()
_cost = {"web": 0.0, "place": 0.0}


def log(message: str) -> None:
    with _print_lock:
        print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def cache_path(kind: str, key: str) -> Path:
    directory = CACHE / kind
    directory.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch for ch in key if ch.isalnum() or ch in "-_") or "unknown"
    return directory / f"{safe}.json"


def cached(kind: str, key: str, producer):
    """디스크 캐시. 실패는 캐시하지 않는다 — 다음 실행에서 다시 시도해야 한다."""
    path = cache_path(kind, key)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8")), True
        except json.JSONDecodeError:
            path.unlink()
    value = producer()
    path.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    return value, False


# ── 1) SEOJI ────────────────────────────────────────────────────────────────
def phase_seoji(books: list[BookInput]) -> None:
    for pos, book in enumerate(books, 1):
        key = book.isbn or f"seq{book.seq}"
        try:
            doc, hit = cached("seoji", key, lambda: (seoji.query(isbn=book.isbn, page_size=1) or [{}])[0])
        except Exception as exc:
            book.raw["seoji_error"] = str(exc)
            log(f"  SEOJI 실패 {book.isbn} {book.title[:20]}: {exc}")
            continue
        if not doc:
            book.raw["seoji_miss"] = True
            continue
        _apply_seoji(book, doc)
        if pos % 50 == 0:
            log(f"  SEOJI {pos}/{len(books)}")


def _apply_seoji(book: BookInput, doc: dict) -> None:
    """seoji.enrich 과 같은 매핑을 캐시된 doc 에 적용한다."""
    def put(attr: str, value: str, label: str) -> None:
        value = (value or "").strip()
        if not value or getattr(book, attr):
            return
        setattr(book, attr, value)
        book.sources[label] = "SEOJI"

    put("title", doc.get("TITLE", ""), "표제")
    put("author_raw", doc.get("AUTHOR", ""), "책임표시")
    put("publisher", doc.get("PUBLISHER", ""), "발행처")
    put("pub_year", (doc.get("PUBLISH_PREDATE") or doc.get("REAL_PUBLISH_DATE") or "")[:4], "발행년")
    put("set_isbn", doc.get("SET_ISBN", ""), "세트ISBN")
    put("isbn_add_code", doc.get("EA_ADD_CODE", ""), "부가기호")
    put("edition", doc.get("EDITION_STMT", ""), "판사항")
    put("series_title", doc.get("SERIES_TITLE", ""), "총서")
    put("series_no", doc.get("SERIES_NO", ""), "총서권호")
    put("vol", doc.get("VOL", ""), "권차")
    put("toc", doc.get("BOOK_TB_CNT", ""), "목차")
    put("summary", doc.get("BOOK_INTRODUCTION") or doc.get("BOOK_SUMMARY", ""), "책소개")

    pages = seoji._pages(doc.get("PAGE", ""))
    if pages:
        put("pages", pages, "면수")
    size = seoji._size_to_cm(doc.get("BOOK_SIZE", ""))
    if size:
        put("size_cm", size, "크기")
    if (doc.get("EBOOK_YN") or "").upper() == "Y" or (doc.get("FORM") or "") not in ("", "종이책"):
        book.raw["form_warning"] = f"SEOJI FORM='{doc.get('FORM')}'"


# ── 2) 웹검색 ───────────────────────────────────────────────────────────────
def phase_web(books: list[BookInput], workers: int, model: str) -> None:
    def work(book: BookInput):
        key = book.isbn or f"seq{book.seq}"

        def produce():
            data, cost = webenrich.lookup(book, model=model)
            with _cost_lock:
                _cost["web"] += cost
            return data

        data, hit = cached("web", key, produce)
        webenrich.apply(book, data)
        book.raw["web"] = data
        return hit

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, b): b for b in books}
        for future in as_completed(futures):
            book = futures[future]
            done += 1
            try:
                future.result()
            except Exception as exc:
                book.raw["web_error"] = str(exc)
                log(f"  웹검색 실패 {book.title[:24]}: {exc}")
            if done % 25 == 0:
                log(f"  웹검색 {done}/{len(books)}  (누적 ${_cost['web']:.2f})")


# ── 2-2) 발행지 ─────────────────────────────────────────────────────────────
def phase_places(books, workers: int, model: str) -> None:
    """출판사 단위로 발행지를 확인해 260 $a·008/15-17을 채운다."""
    store = places.load()
    hints: dict[str, str] = {}
    for b in books:
        name = (b.publisher or "").strip()
        if name:
            hints.setdefault(name, b.title)
    names = sorted(hints)
    unknown = [n for n in names if n not in store.get("places", {})]
    log(f"  출판사 {len(names)}곳 (표에 없는 {len(unknown)}곳 조회)")

    def work(name: str):
        _, cost = places.resolve(name, store=store, model=model, hint=hints.get(name, ""))
        with _cost_lock:
            _cost["place"] += cost

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, n): n for n in unknown}
        for future in as_completed(futures):
            done += 1
            try:
                future.result()
            except Exception as exc:
                log(f"  발행지 조회 실패 {futures[future]}: {exc}")
            if done % 25 == 0:
                log(f"  발행지 {done}/{len(unknown)}  (누적 ${_cost['place']:.2f})")
    places.save(store)

    table = store.get("places", {})
    resolved = 0
    for book in books:
        if book.pub_place:
            continue
        place = table.get((book.publisher or "").strip(), "")
        if place:
            book.pub_place = place
            book.sources["발행지"] = "출판사 소재지 표(웹 확인)"
            resolved += 1
    log(f"  발행지 확인 {resolved}/{len(books)}건")


# ── 3) 장서 DB ──────────────────────────────────────────────────────────────
class Practice:
    """자관 세목 분포 — 강목 단위로 한 번만 조회해 재사용한다."""

    def __init__(self, holdings: Holdings):
        self.holdings = holdings
        self.cache: dict[str, str] = {}
        self.lock = threading.Lock()

    def text(self, kdc_guess: str) -> str:
        base = "".join(ch for ch in (kdc_guess or "") if ch.isdigit())[:3]
        if not base:
            return ""
        with self.lock:
            if base in self.cache:
                return self.cache[base]
        stats = self.holdings.subdivision_stats(base)
        rendered = "\n".join(f"{cls}: {count}건" for cls, count in stats) or "(자관 소장 0건 — 첫 소장)"
        with self.lock:
            self.cache[base] = rendered
        return rendered


def _author_key(book: BookInput) -> str:
    """저자 선례 조회에 쓸 이름 — 구입 목록의 저자란이 가장 깨끗하다(역할어가 없다)."""
    raw = book.raw.get("목록_저자") or book.author_raw or ""
    name = leejaechul.strip_roles(raw)
    return name.split(";")[0].strip()


def phase_holdings(books: list[BookInput], holdings: Holdings, workers: int) -> dict[str, list]:
    """ISBN 기존 소장(ctrl_no 재사용·복본 판정)과 같은 저자 선례(분류 근거)를 모은다."""
    found: dict[str, list] = {}
    lock = threading.Lock()

    def work(book: BookInput):
        rows = holdings.by_isbn(book.isbn) if book.isbn else []
        name = _author_key(book)
        prior = holdings.by_author(name) if name else []
        lines = [
            f"{h.call_no} | {h.title[:40]} | {h.author[:24]} | {h.pub_year or ''}"
            for h in prior if h.call_no
        ][:12]
        with lock:
            found[book.isbn] = [r.__dict__ for r in rows]
            book.raw["저자_선례"] = "\n".join(lines)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(work, books))
    return found


# ── 4) 분류 ─────────────────────────────────────────────────────────────────
def phase_classify(books: list[BookInput], practice: Practice, workers: int, model: str) -> dict[int, dict]:
    results: dict[int, dict] = {}
    lock = threading.Lock()
    done = 0

    def work(book: BookInput):
        key = book.isbn or f"seq{book.seq}"
        web = book.raw.get("web") or {}
        hint = book.kdc_hint or web.get("kdc_guess") or ""
        if web.get("kdc_guess"):
            book.kdc_hint = str(web["kdc_guess"])
        # 재작업 건은 하네스가 권고한 번호의 자관 분포를 보여 준다 — 반려된 옛 번호의
        # 분포를 보여 주면 틀린 강목 안에서 다시 고르게 된다.
        recommended = re.search(r"권고:\s*([\d.]+)", book.rework_note or "")
        practice_text = practice.text(
            recommended.group(1) if recommended else (web.get("kdc_guess") or book.kdc_hint or hint)
        )

        def produce():
            cls = classify_mod.classify(
                book, model=model, practice=practice_text,
                precedents=book.raw.get("저자_선례", ""),
            )
            return cls.__dict__

        data, hit = cached("classify", key, produce)
        with lock:
            results[book.seq] = data

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(work, b): b for b in books}
        for future in as_completed(futures):
            book = futures[future]
            done += 1
            try:
                future.result()
            except Exception as exc:
                book.raw["classify_error"] = str(exc)
                log(f"  분류 실패 {book.title[:24]}: {exc}")
            if done % 25 == 0:
                log(f"  분류 {done}/{len(books)}")
    return results


# ── 5) 조립·QA ──────────────────────────────────────────────────────────────
def assign_author_mark(book: BookInput, cls: Classification, holdings: Holdings,
                       result: Result) -> str:
    base = cls.author_mark_base or book.author_raw
    try:
        mark = leejaechul.author_mark(base, cls.title_proper or book.title)
    except leejaechul.AuthorMarkError as exc:
        result.needs_info.append(f"저자기호: {exc}")
        return ""
    result.author_mark_derivation = mark.derivation

    existing = holdings.by_call_prefix(cls.kdc, mark.mark) if cls.kdc else []
    conflicts = [h for h in existing if h.call_no.split(" ")[1:2] == [mark.mark]]
    if not conflicts:
        return mark.mark

    same_title = [h for h in conflicts if (cls.title_proper or book.title)[:8] in h.title]
    if same_title:
        result.notes.append(
            f"같은 분류·같은 저자기호에 동일 표제 소장 있음({same_title[0].reg_no}) — 복본으로 보고 기호 유지"
        )
        return mark.mark

    for step in (1, -1, 2, -2, 3, -3):
        try:
            adjusted = leejaechul.adjust(mark, step)
        except leejaechul.AuthorMarkError:
            continue
        taken = holdings.by_call_prefix(cls.kdc, adjusted.mark)
        if not any(h.call_no.split(" ")[1:2] == [adjusted.mark] for h in taken):
            result.author_mark_derivation = adjusted.derivation
            result.notes.append(
                f"저자기호 충돌({mark.mark}, 기존 {conflicts[0].reg_no} {conflicts[0].title[:20]}) → {step:+d} 조정"
            )
            return adjusted.mark
    result.needs_info.append(f"저자기호 {mark.mark} 충돌을 ±3 안에서 회피하지 못했습니다.")
    return mark.mark


def _fill_translation(cls: Classification, book: BookInput, result: Result) -> None:
    """번역서인데 원어가 비어 있으면 웹 조사 결과에서 메운다.

    분류 모델이 `is_translation: true`만 세우고 `original_language`를 비워 보내는 일이
    잦다(1차 배치 301건 중 21건). 그대로 두면 041·546이 통째로 빠져 번역서 레코드가
    반쪽이 된다. 웹 조사에도 없으면 지어내지 말고 needs_info로 사서에게 넘긴다.
    """
    if not cls.is_translation:
        return
    web = book.raw.get("web") or {}
    for attr in ("original_language", "original_language_ko", "original_title",
                 "original_author_native"):
        if not getattr(cls, attr) and web.get(attr):
            setattr(cls, attr, str(web[attr]).strip())
            result.notes.append(f"번역 정보 {attr}를 웹 조사 결과에서 보충")
    if not cls.original_language:
        cls.needs_info.append("번역서로 판단되나 원어를 확인하지 못했습니다(041·546 미생성).")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--skip-web", action="store_true")
    args = parser.parse_args()

    load_env()
    started = time.time()
    books = ingest.load(args.input)
    if args.limit:
        books = books[: args.limit]
    log(f"입고 목록 {len(books)}건 — {Path(args.input).name}")

    # 구입 목록의 저자란은 이름만 있고 역할어가 없다("임홍택"). SEOJI의 책임표시
    # ("임홍택 지음", 번역서면 역자까지)가 245 $d/$e에 훨씬 가까우므로 비워 두고
    # SEOJI·웹검색에 채우게 한다. 둘 다 실패하면 목록 값으로 되돌린다.
    for book in books:
        book.raw["목록_저자"] = book.author_raw
        book.author_raw = ""

    holdings = Holdings()
    if not holdings.available:
        log(f"⚠ 장서 DB에 닿지 못했습니다: {holdings.reason}")
    max_ctrl = holdings.max_ctrl_no()
    log(f"장서 DB 최대 제어번호: {max_ctrl}")

    log("1/6 SEOJI 조회")
    phase_seoji(books)

    if not args.skip_web:
        log("2/6 웹검색 보강")
        phase_web(books, args.workers, args.model)
        log(f"  웹검색 비용 ${_cost['web']:.2f}")

    for book in books:
        if not book.author_raw and book.raw.get("목록_저자"):
            book.author_raw = book.raw["목록_저자"]
            book.sources["책임표시"] = "구입 목록(역할어 없음)"

    log("3/6 발행지 확인")
    phase_places(books, args.workers, args.model)
    log(f"  발행지 조회 비용 ${_cost['place']:.2f}")

    log("4/6 장서 DB 조회")
    existing_by_isbn = phase_holdings(books, holdings, args.workers)

    log("5/6 KDC 분류")
    practice = Practice(holdings)
    classifications = phase_classify(books, practice, args.workers, args.model)

    log("6/6 레코드 조립·QA")
    results: list[Result] = []
    next_ctrl = max_ctrl + 1
    now = datetime.now()

    for book in books:
        result = Result(book=book)
        data = classifications.get(book.seq)
        if not data:
            result.status = "error"
            result.error = book.raw.get("classify_error", "분류 결과 없음")
            results.append(result)
            continue

        cls = Classification(**data)
        _fill_translation(cls, book, result)
        result.classification = cls
        result.needs_info += list(cls.needs_info)
        result.notes += list(cls.notes)
        for key in ("seoji_error", "seoji_miss", "web_error", "form_warning"):
            if book.raw.get(key):
                result.notes.append(f"{key}: {book.raw[key]}")

        prior = existing_by_isbn.get(book.isbn) or []
        if prior and prior[0].get("ctrl_no"):
            ctrl_no = str(prior[0]["ctrl_no"])
            result.notes.append(
                f"같은 ISBN 기존 소장 {len(prior)}건 — 제어번호 {ctrl_no} 재사용, 복본 입고로 처리"
            )
        else:
            ctrl_no = str(next_ctrl)
            next_ctrl += 1

        mark = assign_author_mark(book, cls, holdings, result)
        result.author_mark = mark
        result.call_no = f"{cls.kdc} {mark}".strip()

        try:
            record = marc.build(book, cls, mark, ctrl_no, now=now)
        except Exception as exc:
            result.status = "error"
            result.error = f"레코드 조립 실패: {exc}"
            results.append(result)
            continue
        result.record = record
        failures, place_gaps = qa.split_place_gaps(qa.check(record, book, cls, mark))
        result.qa_failures = failures
        if place_gaps:
            result.needs_info = list(result.needs_info) + ["발행지 미확인 — 판권지 확인 필요"]

        if result.qa_failures:
            result.status = "qa_failed"
        elif result.needs_info or cls.confidence != "high":
            result.status = "needs_info"
        else:
            result.status = "ok"
        results.append(result)

    write_outputs(Path(args.out), results, started)
    return 0


def write_outputs(out: Path, results: list[Result], started: float) -> None:
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now()

    lines = [
        "# 2026년 제4차 정기도서 구입 목록(일반) — B-04-W 자료조직 결과",
        f"# 생성 {stamp:%Y-%m-%d %H:%M} / {len(results)}건",
        "# ※ LDR·008의 #는 공백 1칸이다(적재 시 복원)",
        "# ⚠ 사서 검토 전 초안. status가 ok가 아닌 건은 처리현황.csv에서 사유를 확인할 것.",
        "",
    ]
    for pos, result in enumerate(results, 1):
        book = result.book
        lines.append("=" * 80)
        lines.append(f"[{pos}] {book.title}  ({', '.join(book.reg_nos) or '등록번호 없음'}) — {result.status}")
        lines.append("=" * 80)
        if result.record:
            lines.append(marc.render(result.record))
        else:
            lines.append(f"(레코드 없음) {result.error}")
        if result.classification and result.classification.kdc_path:
            lines.append(f"# 분류경로: {result.classification.kdc_path}")
        if result.author_mark_derivation:
            lines.append(f"# 저자기호: {result.author_mark_derivation}")
        for note in result.notes:
            lines.append(f"# 메모: {note}")
        for item in result.needs_info:
            lines.append(f"# needs_info: {item}")
        for item in result.qa_failures:
            lines.append(f"# QA: {item}")
        lines.append("")
    (out / "records.txt").write_text("\n".join(lines), encoding="utf-8")

    with open(out / "처리현황.csv", "w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "순", "등록번호", "제어번호", "서명", "저자", "출판사", "발행지", "ISBN",
            "KDC", "청구기호", "상태", "확신도", "QA 지적", "needs_info", "메모",
        ])
        for result in results:
            book = result.book
            cls = result.classification
            writer.writerow([
                book.seq,
                ";".join(book.reg_nos),
                (result.record.control.get("001", "") if result.record else ""),
                book.title,
                book.author_raw,
                book.publisher,
                book.pub_place,
                book.isbn,
                cls.kdc if cls else "",
                result.call_no,
                result.status,
                cls.confidence if cls else "",
                " / ".join(result.qa_failures),
                " / ".join(result.needs_info),
                " / ".join(result.notes),
            ])

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    summary = [
        f"처리 {len(results)}건 / {time.time() - started:.0f}초 / "
        f"웹검색 ${_cost['web']:.2f} + 발행지 ${_cost['place']:.2f}",
        "상태: " + ", ".join(f"{k} {v}건" for k, v in sorted(counts.items())),
    ]
    (out / "요약.txt").write_text("\n".join(summary) + "\n", encoding="utf-8")
    log("\n".join(summary))
    log(f"출력: {out}")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("중단됨 — 캐시는 남아 있으니 같은 명령으로 이어서 실행하면 됩니다.")
        sys.exit(130)
    except Exception:
        traceback.print_exc()
        sys.exit(1)
