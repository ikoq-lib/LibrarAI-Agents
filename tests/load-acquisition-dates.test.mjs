import test from "node:test";
import assert from "node:assert/strict";

import {
  estimateDate,
  mapHeader,
  missingMonths,
  parseRanges,
  regNoToNum,
  validateRanges,
  HALF_MID_DAY,
  PRE_2019_DATE,
} from "../scripts/load-acquisition-dates.mjs";

const HEADER = ["연도", "월", "기간", "시작등록번호EM", "끝등록번호EM"];

test("등록번호 표기가 달라도 같은 숫자로 읽는다", () => {
  // books 에는 EM181905(8자리)와 EM0181905(9자리) 표기가 섞여 있고 숫자값은 고유하다.
  assert.equal(regNoToNum("EM181905"), 181905);
  assert.equal(regNoToNum("EM0181905"), 181905);
  assert.equal(regNoToNum("181905"), 181905);
  assert.equal(regNoToNum("  em181905 "), 181905);
  assert.equal(regNoToNum("NB0001"), null);
  assert.equal(regNoToNum(""), null);
});

test("반월 구간의 중앙값을 추정일로 쓴다", () => {
  assert.equal(estimateDate(2019, 1, "상"), "2019-01-08");
  assert.equal(estimateDate(2026, 12, "하"), "2026-12-23");
  assert.equal(estimateDate(2020, 3, "중"), null);
  assert.deepEqual(HALF_MID_DAY, { 상: 8, 하: 23 });
});

test("헤더 순서가 바뀌어도 컬럼을 찾는다", () => {
  const map = mapHeader(["끝등록번호EM", "연도", "시작등록번호EM", "기간", "월"]);
  assert.equal(map.endNo, 0);
  assert.equal(map.year, 1);
  assert.equal(map.startNo, 2);
  assert.equal(map.half, 3);
  assert.equal(map.month, 4);
});

test("구간 행을 파싱하고 형식이 깨진 행은 제외한다", () => {
  const { periods, skipped } = parseRanges([
    HEADER,
    ["2019", "1", "상", "EM161032", "EM161500"],
    ["2019", "1", "하", "EM161501", "EM162000"],
    ["2019", "13", "상", "EM162001", "EM162100"],  // 월 범위 밖
    ["2019", "2", "중", "EM162101", "EM162200"],   // 반기 값 오류
    ["", "", "", "", ""],                           // 빈 행은 조용히 건너뜀
  ]);
  assert.equal(periods.length, 2);
  assert.equal(skipped.length, 2);
  assert.deepEqual(periods[0], {
    year: 2019, month: 1, half: "상",
    startNum: 161032, endNum: 161500, estDate: "2019-01-08",
  });
});

test("필수 컬럼이 없으면 오류를 낸다", () => {
  assert.throws(() => parseRanges([["연도", "월"], ["2019", "1"]]), /필수 컬럼/);
});

test("정상 구간표는 오류 없이 통과한다", () => {
  const { periods } = parseRanges([
    HEADER,
    ["2019", "1", "상", "EM100", "EM199"],
    ["2019", "1", "하", "EM200", "EM299"],
    ["2019", "2", "상", "EM300", "EM399"],
  ]);
  const r = validateRanges(periods);
  assert.deepEqual(r.issues, []);
  assert.deepEqual(r.gaps, []);
  assert.equal(r.minNum, 100);
  assert.equal(r.maxNum, 399);
});

test("겹치는 구간을 잡아낸다", () => {
  const { periods } = parseRanges([
    HEADER,
    ["2019", "1", "상", "EM100", "EM250"],
    ["2019", "1", "하", "EM200", "EM299"],
  ]);
  const r = validateRanges(periods);
  assert.equal(r.issues.filter((i) => i.kind === "overlap").length, 1);
});

test("끝번호가 시작번호보다 작으면 잡아낸다", () => {
  const { periods } = parseRanges([HEADER, ["2019", "1", "상", "EM300", "EM200"]]);
  const r = validateRanges(periods);
  assert.equal(r.issues.filter((i) => i.kind === "inverted").length, 1);
});

test("시간순으로 번호가 거꾸로 가면 잡아낸다", () => {
  // 등록번호는 입수 순서대로 매겨지므로 뒤 시기의 시작번호가 더 작을 수 없다.
  const { periods } = parseRanges([
    HEADER,
    ["2019", "2", "상", "EM100", "EM199"],
    ["2019", "1", "상", "EM300", "EM399"],
  ]);
  const r = validateRanges(periods);
  assert.equal(r.issues.filter((i) => i.kind === "non_monotonic").length, 1);
});

test("번호 공백은 오류가 아니라 정보로 보고한다", () => {
  const { periods } = parseRanges([
    HEADER,
    ["2019", "1", "상", "EM100", "EM199"],
    ["2019", "1", "하", "EM300", "EM399"],
  ]);
  const r = validateRanges(periods);
  assert.deepEqual(r.issues, []);
  assert.deepEqual(r.gaps, [{ from: 200, to: 299, count: 100 }]);
});

test("구간이 없는 달을 찾아낸다", () => {
  const { periods } = parseRanges([
    HEADER,
    ["2019", "1", "상", "EM100", "EM199"],
    ["2019", "3", "상", "EM200", "EM299"],
    ["2019", "4", "상", "EM300", "EM399"],
  ]);
  assert.deepEqual(missingMonths(periods), ["2019-02"]);
});

test("연도를 넘어가는 구간 공백도 찾는다", () => {
  const { periods } = parseRanges([
    HEADER,
    ["2019", "11", "상", "EM100", "EM199"],
    ["2020", "2", "상", "EM200", "EM299"],
  ]);
  assert.deepEqual(missingMonths(periods), ["2019-12", "2020-01"]);
});

test("2019년 이전 대체값은 대출 데이터 시작(2024-01-01)보다 앞선다", () => {
  // 노출기간은 max(대출데이터 시작일, acquired_date) 부터 세므로,
  // 대체값이 2024-01-01 보다 앞서기만 하면 어떤 값이든 현재 회전율은 동일하다.
  assert.ok(PRE_2019_DATE < "2024-01-01");
});
