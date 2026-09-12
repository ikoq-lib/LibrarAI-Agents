/**
 * api/wishlist-requests.js 통합 테스트 — 실제 Supabase 를 읽는다.
 *
 * 순수 함수 테스트(generate-wishlist-requests.test.mjs)로는 잡히지 않는 SQL 결함을 막는다.
 * 실제로 2026-09-12 에 month_count 를 윈도 함수로 계산해 주차 조회에서 월 누계가
 * 항상 그 주 건수로 나오는 결함이 있었고, 단위 테스트는 이를 통과시켰다.
 *
 * SUPABASE_DB_PASSWORD 가 없으면 전부 건너뛴다(로컬에서 자격증명 없이 돌려도 안전).
 */
import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import fs from "node:fs";
import path from "node:path";

const require = createRequire(import.meta.url);

// .env.local 을 올려 로컬에서도 자격증명이 있으면 실제로 돌게 한다.
for (const name of [".env", ".env.local"]) {
  const file = path.join(process.cwd(), name);
  if (!fs.existsSync(file)) continue;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].trim();
  }
}

const skip = process.env.SUPABASE_DB_PASSWORD
  ? false
  : "SUPABASE_DB_PASSWORD 없음 — DB 통합 테스트 건너뜀";

const handler = require("../api/wishlist-requests.js");

/** Vercel 핸들러를 호출하고 {code, body} 를 돌려준다. */
async function call(query) {
  let code = null, body = null;
  const res = {
    setHeader() {}, end() { return this; },
    status(c) { code = c; return this; },
    json(o) { body = o; return this; },
  };
  await handler({ method: "GET", query }, res);
  return { code, body };
}

test("주차 조회가 신청 건과 서지 스냅샷을 돌려준다", { skip }, async () => {
  const { code, body } = await call({});
  assert.equal(code, 200);
  assert.equal(body.mode, "week");
  if (!body.count) return; // 아직 적재 전이면 형식만 확인하고 끝낸다.
  const r = body.requests[0];
  for (const f of ["id", "request_week", "requested_at", "patron_id", "patron_label",
                   "title", "status", "month_count", "format_verified"]) {
    assert.ok(f in r, `${f} 열이 없다`);
  }
  assert.ok(body.requests.every(x => x.request_week === body.week), "다른 주차가 섞였다");
});

test("month_count 는 그 주가 아니라 해당 월 전체를 센다", { skip }, async () => {
  // 이 테스트가 막는 결함: 윈도 함수는 where 로 걸러진 뒤에 계산되므로
  // 주차 조회에서 월 누계가 그 주 건수로 축소된다 → 월 3권 초과를 영영 못 잡는다.
  const { body } = await call({});
  if (!body.count) return;

  const weekCounts = new Map();
  for (const r of body.requests) weekCounts.set(r.patron_id, (weekCounts.get(r.patron_id) ?? 0) + 1);

  // 같은 신청자가 이전 주차에도 신청한 적이 있으면 월 누계가 이번 주 건수보다 커야 한다.
  const month = body.requests[0].requested_at.slice(0, 7);
  const { body: monthBody } = await call({ mode: "month", month });
  const monthCounts = new Map();
  for (const r of monthBody.requests) monthCounts.set(r.patron_id, (monthCounts.get(r.patron_id) ?? 0) + 1);

  for (const r of body.requests) {
    const expected = monthCounts.get(r.patron_id);
    if (expected === undefined) continue; // 신청월이 조회한 달과 다른 건(월 경계 주차)
    assert.equal(r.month_count, expected,
      `${r.patron_label} 월 누계가 ${r.month_count} 인데 ${month} 실제 건수는 ${expected}`);
    assert.ok(r.month_count >= weekCounts.get(r.patron_id),
      `월 누계(${r.month_count})가 주간 건수(${weekCounts.get(r.patron_id)})보다 작다`);
  }
});

test("월 조회는 요청한 달만 돌려준다", { skip }, async () => {
  const { code, body } = await call({ mode: "month", month: "2026-09" });
  assert.equal(code, 200);
  assert.ok(body.requests.every(r => r.requested_at.startsWith("2026-09")),
    "9월이 아닌 신청이 섞였다");
});

test("주차별 집계가 목록 건수와 맞는다", { skip }, async () => {
  const { body: summary } = await call({ mode: "summary" });
  if (!summary.count) return;
  const week = summary.rows[0].request_week;
  const { body: detail } = await call({ week });
  assert.equal(detail.count, summary.rows[0].requested,
    `${week} 집계 ${summary.rows[0].requested}건 vs 목록 ${detail.count}건`);
});

test("신청자 실명은 마스킹하고 목업 이름만 그대로 준다", { skip }, async () => {
  const { body } = await call({});
  if (!body.count) return;
  for (const r of body.requests) {
    assert.ok(r.patron_label, "신청자 라벨이 비었다");
    // 목업은 테스트N, 실명이 들어오면 성 한 글자 + 별표여야 한다.
    const ok = /^테스트\d+$/.test(r.patron_label) || /^.\*+$/.test(r.patron_label) || r.patron_label.length === 1;
    assert.ok(ok, `마스킹되지 않은 이름: ${r.patron_label}`);
  }
});

test("모르는 mode 는 400 으로 거절한다", { skip }, async () => {
  const { code, body } = await call({ mode: "bogus" });
  assert.equal(code, 400);
  assert.match(body.error, /week/);
});
