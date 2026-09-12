import test from "node:test";
import assert from "node:assert/strict";

import {
  addDays,
  assignPatrons,
  buildPatrons,
  fmtDate,
  isoWeekNo,
  makeRng,
  mondayOf,
  parseDate,
  pickRequestSize,
  randomRequestedAt,
  shuffle,
  targetWeek,
} from "../scripts/generate-wishlist-requests.mjs";

const patronPool = (n) =>
  Array.from({ length: n }, (_, i) => ({ id: i + 1, name: `테스트${i + 1}`, age: 30, age_group: "성인", gender: "남" }));

const bookPool = (n) =>
  Array.from({ length: n }, (_, i) => ({
    ea_isbn: String(9788900000000 + i),
    title: `책 ${i + 1}`,
    author: "저자",
    publisher: "출판사",
    pre_price: 15000,
    form_detail: "무선제본",
  }));

// ---------------------------------------------------------------------------
// 주차 계산
// ---------------------------------------------------------------------------

test("주중 어느 날이든 그 주 월요일을 찾는다", () => {
  assert.equal(fmtDate(mondayOf(parseDate("2026-09-07"))), "2026-09-07"); // 월
  assert.equal(fmtDate(mondayOf(parseDate("2026-09-10"))), "2026-09-07"); // 목
  assert.equal(fmtDate(mondayOf(parseDate("2026-09-12"))), "2026-09-07"); // 토
});

test("일요일은 전주가 아니라 그 주의 마지막 날로 본다 (월~일 접수 사이클)", () => {
  // getUTCDay 는 일요일이 0 이라 -1 을 그대로 쓰면 다음 주 월요일이 나온다.
  assert.equal(fmtDate(mondayOf(parseDate("2026-09-13"))), "2026-09-07");
});

test("화요일에 돌면 접수가 끝난 직전 월~일을 고른다", () => {
  // 2026-09-15 는 화요일. 이번 주 월요일(09-14)은 어제라 접수가 안 끝났다.
  assert.equal(fmtDate(targetWeek(parseDate("2026-09-15"))), "2026-09-07");
});

test("대상 주차는 월~일 7일 구간이다", () => {
  const week = targetWeek(parseDate("2026-09-15"));
  assert.equal(fmtDate(week), "2026-09-07");
  assert.equal(fmtDate(addDays(week, 6)), "2026-09-13");
  assert.equal(addDays(week, 6).getUTCDay(), 0); // 일요일
});

test("ISO 주차 번호를 매긴다", () => {
  assert.deepEqual(isoWeekNo(parseDate("2026-01-05")), { year: 2026, week: 2 });
  assert.deepEqual(isoWeekNo(parseDate("2026-09-07")), { year: 2026, week: 37 });
});

test("YYYY-MM-DD 가 아니면 null 을 돌려준다", () => {
  assert.equal(parseDate("2026/09/07"), null);
  assert.equal(parseDate("20260907"), null);
  assert.equal(parseDate(""), null);
  assert.equal(parseDate(undefined), null);
});

// ---------------------------------------------------------------------------
// 접수 시각
// ---------------------------------------------------------------------------

test("접수 시각은 대상 주 7일 안에서 개관 시간(KST 09~21시)에 들어간다", () => {
  const rng = makeRng(7);
  const monday = parseDate("2026-09-07");
  const end = addDays(monday, 7);
  for (let i = 0; i < 300; i++) {
    const at = randomRequestedAt(monday, rng);
    assert.ok(at >= monday && at < end, `주 범위 밖: ${at.toISOString()}`);
    const hourKst = new Date(at.getTime() + 9 * 3600000).getUTCHours();
    assert.ok(hourKst >= 9 && hourKst <= 21, `개관 시간 밖: ${hourKst}시`);
  }
});

test("접수 시각은 한 요일에 몰리지 않고 주 전체에 흩어진다", () => {
  const rng = makeRng(11);
  const monday = parseDate("2026-09-07");
  const days = new Set();
  for (let i = 0; i < 200; i++) days.add(randomRequestedAt(monday, rng).getUTCDay());
  assert.equal(days.size, 7);
});

// ---------------------------------------------------------------------------
// 신청자 풀
// ---------------------------------------------------------------------------

test("모자란 인원만 이어 붙여 만든다", () => {
  const fresh = buildPatrons(12, 40, makeRng(3));
  assert.equal(fresh.length, 28);
  assert.equal(fresh[0].name, "테스트13");
  assert.equal(fresh.at(-1).name, "테스트40");
});

test("신청자는 연령대와 나이가 맞물린다", () => {
  const bands = { 유아: [4, 7], 어린이: [8, 13], 청소년: [14, 18], 성인: [19, 75] };
  for (const p of buildPatrons(0, 400, makeRng(5))) {
    const [min, max] = bands[p.age_group];
    assert.ok(p.age >= min && p.age <= max, `${p.age_group} ${p.age}세`);
    assert.ok(p.gender === "남" || p.gender === "여");
  }
});

test("연령 구성이 수서 기준 비율(성인50·어린이25·유아15·청소년10)에 가깝다", () => {
  const patrons = buildPatrons(0, 2000, makeRng(9));
  const share = (g) => patrons.filter((p) => p.age_group === g).length / patrons.length;
  assert.ok(Math.abs(share("성인") - 0.50) < 0.05, `성인 ${share("성인")}`);
  assert.ok(Math.abs(share("어린이") - 0.25) < 0.05, `어린이 ${share("어린이")}`);
  assert.ok(Math.abs(share("유아") - 0.15) < 0.05, `유아 ${share("유아")}`);
  assert.ok(Math.abs(share("청소년") - 0.10) < 0.05, `청소년 ${share("청소년")}`);
});

// ---------------------------------------------------------------------------
// 배정
// ---------------------------------------------------------------------------

test("모든 책이 정확히 한 번씩 배정된다", () => {
  const books = bookPool(25);
  const pairs = assignPatrons(books, patronPool(40), makeRng(1));
  assert.equal(pairs.length, 25);
  assert.equal(new Set(pairs.map((p) => p.book.ea_isbn)).size, 25);
});

test("한 사람이 한 주에 3권을 넘게 받지 않는다", () => {
  const pairs = assignPatrons(bookPool(30), patronPool(12), makeRng(2));
  const counts = new Map();
  for (const { patron } of pairs) counts.set(patron.id, (counts.get(patron.id) ?? 0) + 1);
  for (const [id, n] of counts) assert.ok(n <= 3, `신청자 ${id} 가 ${n}권`);
});

test("풀이 넉넉하면 여러 신청자에게 흩어진다", () => {
  const pairs = assignPatrons(bookPool(25), patronPool(40), makeRng(4));
  // 1인 1~3권(평균 1.5)이라 25권이면 대략 17명 안팎으로 퍼진다.
  // 한 사람에게 몰리지도(=적은 인원), 전원 1권씩 균등하지도(=25명) 않아야 한다.
  const distinct = new Set(pairs.map((p) => p.patron.id)).size;
  assert.ok(distinct >= 12 && distinct <= 22, `신청자 ${distinct}명`);
});

test("한 주에 2권 이상 신청한 사람이 섞여 있다", () => {
  // 전원 1권씩 균등 배분은 실제 신청 분포와 다르다 — 몰아 신청하는 사람이 있어야 한다.
  const pairs = assignPatrons(bookPool(26), patronPool(40), makeRng(4));
  const counts = new Map();
  for (const { patron } of pairs) counts.set(patron.id, (counts.get(patron.id) ?? 0) + 1);
  assert.ok([...counts.values()].some((n) => n >= 2), "전원이 1권씩만 신청했다");
});

test("신청 권수는 1~3권 사이에서 정해진다", () => {
  const rng = makeRng(21);
  const seen = new Set();
  for (let i = 0; i < 500; i++) {
    const n = pickRequestSize(rng);
    assert.ok(n >= 1 && n <= 3, `${n}권`);
    seen.add(n);
  }
  assert.deepEqual([...seen].sort(), [1, 2, 3]);
});

test("풀보다 책이 많으면 조용히 버리지 않고 실패한다", () => {
  // 5명 × 3권 = 15권이 상한. 16권째는 배정할 곳이 없다.
  assert.throws(() => assignPatrons(bookPool(16), patronPool(5), makeRng(6)), /신청자 풀이 부족/);
});

test("신청자 풀이 비면 실패한다", () => {
  assert.throws(() => assignPatrons(bookPool(3), [], makeRng(6)), /비어 있습니다/);
});

test("같은 시드는 같은 배정을 낸다", () => {
  const a = assignPatrons(bookPool(25), patronPool(40), makeRng(42));
  const b = assignPatrons(bookPool(25), patronPool(40), makeRng(42));
  assert.deepEqual(a.map((p) => [p.book.ea_isbn, p.patron.id]), b.map((p) => [p.book.ea_isbn, p.patron.id]));
});

test("다른 시드는 다른 배정을 낸다", () => {
  const a = assignPatrons(bookPool(25), patronPool(40), makeRng(1));
  const b = assignPatrons(bookPool(25), patronPool(40), makeRng(2));
  assert.notDeepEqual(a.map((p) => p.patron.id), b.map((p) => p.patron.id));
});

// ---------------------------------------------------------------------------
// 난수 유틸
// ---------------------------------------------------------------------------

test("shuffle 은 원본을 건드리지 않고 원소를 보존한다", () => {
  const src = [1, 2, 3, 4, 5, 6, 7, 8];
  const out = shuffle(src, makeRng(8));
  assert.deepEqual(src, [1, 2, 3, 4, 5, 6, 7, 8]);
  assert.deepEqual([...out].sort((x, y) => x - y), src);
});

test("여러 주에 걸쳐 돌리면 1인 월 3권 초과가 실제로 발생한다", () => {
  // FN-04 한도 검증이 일할 거리가 생기는지 — 고정 풀 재사용을 택한 이유다.
  const rng = makeRng(13);
  const counts = new Map();
  for (let week = 0; week < 4; week++) {
    for (const { patron } of assignPatrons(bookPool(25), patronPool(40), rng)) {
      counts.set(patron.id, (counts.get(patron.id) ?? 0) + 1);
    }
  }
  const over = [...counts.values()].filter((n) => n > 3);
  assert.ok(over.length > 0, "월 3권 초과 신청자가 한 명도 없다");
});
