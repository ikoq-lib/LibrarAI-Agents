import test from "node:test";
import assert from "node:assert/strict";

import {
  applyCollectFilter,
  fetchPage,
  harvest,
  shiftDays,
  toAddCode,
  toCatalogRow,
  toDate,
  toInt,
  toIsbn13,
} from "../scripts/harvest-seoji-catalog.mjs";

const CERT = "test-key";

/** SEOJI 응답을 흉내내는 fetch. pages 는 페이지별 docs 배열. */
function fakeFetch(pages, { total = 1_000_000, onCall } = {}) {
  return async (url) => {
    const pageNo = Number(new URL(url).searchParams.get("page_no"));
    onCall?.(url);
    const docs = pages[pageNo - 1] ?? [];
    return { text: async () => JSON.stringify({ TOTAL_COUNT: total, PAGE_NO: pageNo, docs }) };
  };
}

const doc = (isbn, inputDate, extra = {}) => ({
  EA_ISBN: isbn,
  TITLE: `책 ${isbn}`,
  PUBLISHER: "테스트출판사",
  INPUT_DATE: inputDate,
  PUBLISH_PREDATE: "20260801",
  EA_ADD_CODE: "03810",
  FORM: "종이책",
  ...extra,
});

test("YYYYMMDD 를 날짜로 바꾸고 달력에 없는 날은 버린다", () => {
  assert.equal(toDate("20260801"), "2026-08-01");
  assert.equal(toDate("20260229"), null); // 2026년은 평년
  assert.equal(toDate("20261301"), null);
  assert.equal(toDate("2026-08-01"), null);
  assert.equal(toDate(""), null);
});

test("가격·쪽수에서 숫자만 뽑는다", () => {
  assert.equal(toInt("50000"), 50000);
  assert.equal(toInt("18,000원"), 18000);
  assert.equal(toInt(""), null);
  assert.equal(toInt("미정"), null);
});

test("ISBN13 은 숫자 13자리만 통과시킨다", () => {
  assert.equal(toIsbn13("9791122034219"), "9791122034219");
  assert.equal(toIsbn13("979-11-220-3421-9"), "9791122034219");
  assert.equal(toIsbn13("123456789"), null);
  assert.equal(toIsbn13(""), null);
});

test("부가기호는 5자리만 통과시킨다", () => {
  assert.equal(toAddCode("93360"), "93360");
  assert.equal(toAddCode("9 3 360"), "93360");
  assert.equal(toAddCode("0381"), null);
  assert.equal(toAddCode("03810A"), null);
});

test("SEOJI 레코드를 book_catalog 행으로 바꾼다", () => {
  const row = toCatalogRow({
    EA_ISBN: "9791122034219",
    SET_ISBN: "",
    TITLE: "탄원서닷컴③",
    AUTHOR: "저자 : 법학도사",
    PUBLISHER: "도서출판 법률북스",
    PUBLISH_PREDATE: "20260801",
    INPUT_DATE: "20260727",
    PRE_PRICE: "50000",
    FORM_DETAIL: "무선제본",
    PAGE: "176",
    BOOK_SIZE: "182*257",
    EA_ADD_CODE: "93360",
  });
  assert.equal(row.ea_isbn, "9791122034219");
  assert.equal(row.set_isbn, null);
  assert.equal(row.title, "탄원서닷컴③");
  assert.equal(row.publish_predate, "2026-08-01");
  assert.equal(row.input_date, "2026-07-27");
  assert.equal(row.pre_price, 50000);
  assert.equal(row.page_count, 176);
  assert.equal(row.ea_add_code, "93360");
});

test("권차는 SERIES_NO, SET_EXPRESSION, VOL 순으로 채운다", () => {
  const base = { EA_ISBN: "9791122034219", TITLE: "x" };
  assert.equal(toCatalogRow({ ...base, SERIES_NO: "3", VOL: "9" }).series_no, "3");
  assert.equal(toCatalogRow({ ...base, SET_EXPRESSION: "상", VOL: "9" }).series_no, "상");
  assert.equal(toCatalogRow({ ...base, VOL: "9" }).series_no, "9");
  assert.equal(toCatalogRow(base).series_no, null);
});

test("ISBN 이나 제목이 없는 레코드는 버린다", () => {
  assert.equal(toCatalogRow({ EA_ISBN: "", TITLE: "제목" }), null);
  assert.equal(toCatalogRow({ EA_ISBN: "9791122034219", TITLE: "" }), null);
});

test("날짜를 일수만큼 뒤로 옮긴다", () => {
  assert.equal(shiftDays("2026-08-26", 3), "2026-08-23");
  assert.equal(shiftDays("2026-03-01", 1), "2026-02-28");
  assert.equal(shiftDays("2026-01-01", 1), "2025-12-31");
});

test("워터마크보다 오래된 등록일이 나오면 수집을 멈춘다", async () => {
  const pages = [
    [doc("9791122034001", "20260825"), doc("9791122034002", "20260824")],
    [doc("9791122034003", "20260823"), doc("9791122034004", "20260820")],
    [doc("9791122034005", "20260819")],
  ];
  const calls = [];
  const res = await harvest({
    watermark: "2026-08-22",
    certKey: CERT,
    pageSize: 2,
    fetchImpl: fakeFetch(pages, { onCall: (u) => calls.push(u) }),
    log: () => {},
  });
  // 2페이지에서 20260820 이 워터마크 미만이라 3페이지는 요청하지 않는다.
  assert.equal(calls.length, 2);
  // 워터마크 미만 레코드는 결과에서 제외된다.
  assert.deepEqual(res.rows.map((r) => r.ea_isbn).sort(),
    ["9791122034001", "9791122034002", "9791122034003"]);
  assert.equal(res.reachedWatermark, true);
});

test("페이지 경계 중복은 ISBN 기준으로 하나만 남는다", async () => {
  const pages = [
    [doc("9791122034001", "20260825"), doc("9791122034002", "20260824")],
    [doc("9791122034002", "20260824"), doc("9791122034003", "20260820")],
  ];
  const res = await harvest({
    watermark: "2026-08-22", certKey: CERT, pageSize: 2,
    fetchImpl: fakeFetch(pages), log: () => {},
  });
  assert.equal(res.rows.length, 2);
});

test("페이지 상한에 걸리면 경고를 남기고 멈춘다", async () => {
  const pages = [[doc("9791122034001", "20260825")], [doc("9791122034002", "20260825")]];
  const logs = [];
  const res = await harvest({
    watermark: "2020-01-01", maxPages: 1, certKey: CERT, pageSize: 1,
    fetchImpl: fakeFetch(pages), log: (m) => logs.push(m),
  });
  assert.equal(res.pages, 1);
  assert.equal(res.reachedWatermark, false);
  assert.ok(logs.some((l) => l.includes("페이지 상한")));
});

test("빈 페이지를 만나면 중단한다", async () => {
  const res = await harvest({
    watermark: "2020-01-01", certKey: CERT, pageSize: 1,
    fetchImpl: fakeFetch([[doc("9791122034001", "20260825")], []]), log: () => {},
  });
  assert.equal(res.pages, 2);
  assert.equal(res.rows.length, 1);
});

test("SEOJI 오류 응답은 3회 재시도 후 실패한다", async () => {
  let calls = 0;
  const failing = async () => {
    calls++;
    return { text: async () => JSON.stringify({ RESULT: "ERROR", ERR_CODE: "013", ERR_MESSAGE: "쪽당 출력건수는 1000건 미만입니다." }) };
  };
  await assert.rejects(() => fetchPage(1, CERT, failing), /013/);
  assert.equal(calls, 3);
});

test("일시적 실패 뒤 성공하면 결과를 돌려준다", async () => {
  let calls = 0;
  const flaky = async (url) => {
    calls++;
    if (calls === 1) return { text: async () => "" };
    return fakeFetch([[doc("9791122034001", "20260825")]])(url);
  };
  const res = await fetchPage(1, CERT, flaky);
  assert.equal(res.docs.length, 1);
  assert.equal(calls, 2);
});

test("요청에 종이책 필터와 등록일 역순 정렬이 들어간다", async () => {
  let seen;
  await fetchPage(1, CERT, fakeFetch([[]], { onCall: (u) => { seen = new URL(u); } }));
  assert.equal(seen.searchParams.get("form"), "종이책");
  assert.equal(seen.searchParams.get("sort"), "INPUT_DATE");
  assert.equal(seen.searchParams.get("order_by"), "DESC");
  assert.equal(seen.searchParams.get("page_size"), "1000");
  assert.equal(seen.searchParams.get("result_style"), "json");
});

test("미수집 유형을 부가기호 1·2자리로 걸러낸다", () => {
  const rows = [
    { ea_isbn: "1", ea_add_code: "03810" }, // 교양 단행본 - 수집
    { ea_isbn: "2", ea_add_code: "53810" }, // 중고교 학습참고서 - 제외
    { ea_isbn: "3", ea_add_code: "63810" }, // 초등 학습참고서 - 제외
    { ea_isbn: "4", ea_add_code: "93360" }, // 전문서 - 제외
    { ea_isbn: "5", ea_add_code: "08810" }, // 혼합·전자자료 - 제외
    { ea_isbn: "6", ea_add_code: null },    // 부가기호 없음 - 판단 불가라 수집
  ];
  const { kept, skipped } = applyCollectFilter(rows, new Set(["5", "6", "9"]), new Set(["8"]));
  assert.deepEqual(kept.map((r) => r.ea_isbn), ["1", "6"]);
  assert.deepEqual(skipped.map((r) => r.ea_isbn), ["2", "3", "4", "5"]);
});
