/**
 * B-02 주간 처리 집계 테스트.
 *
 * 대상 코드는 LibrarAI.html 안에 있으므로 복사본을 만들지 않고 원본에서 함수를 꺼내 쓴다.
 * 복사해두면 HTML 쪽만 바뀌었을 때 테스트가 옛 코드를 통과시켜 검증이 아니게 된다.
 *
 * 막으려는 결함(2026-09-12 실측): 모델이 건별 판정은 25건 정확히 냈는데 하단 요약만
 * "반려 10 / 수동 7"(실제 9 / 8)로 어긋났다. 사서가 요약만 보면 틀린 수치를 가져간다.
 */
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const html = fs.readFileSync(path.join(process.cwd(), "LibrarAI.html"), "utf8");

/** HTML 에서 `      const <name> = ` 로 시작해 같은 들여쓰기의 닫는 줄까지 잘라낸다. */
function grab(name, closing = "\n      };") {
  const start = html.indexOf(`      const ${name} = `);
  assert.ok(start >= 0, `${name} 을 LibrarAI.html 에서 찾지 못했습니다`);
  const end = html.indexOf(closing, start);
  assert.ok(end > start, `${name} 의 끝을 찾지 못했습니다`);
  return html.slice(start, end + closing.length).replace(/^      const /, "const ");
}

const src = [
  grab("B02_VERDICT_RE", ";"),
  grab("B02_VERDICT_HEADER_KEYS", ";"),
  grab("b02NormalizeVerdict"),
  grab("extractB02Requests"),
  grab("summarizeB02Verdicts"),
  "module.exports = { b02NormalizeVerdict, extractB02Requests, summarizeB02Verdicts };",
].join("\n");

// summarizeB02Verdicts 는 B-03 인계용 배치 레지스트리(b01RegisterBatch)를 부른다.
// 실물은 localStorage 에 기대므로, 등록 내용을 붙잡아 두는 대역을 주입해 인계까지 검사한다.
let lastBatch = null;
const fakeRegister = (items, prefix) => {
  lastBatch = { items, prefix };
  return { id: `${prefix}-20260912-1`, items };
};
const resetBatch = () => { lastBatch = null; };

const mod = { exports: {} };
new Function("module", "exports", "b01RegisterBatch", src)(mod, mod.exports, fakeRegister);
const { b02NormalizeVerdict, extractB02Requests, summarizeB02Verdicts } = mod.exports;

/** 웹앱이 실제로 붙이는 신청 목록 블록과 같은 모양을 만든다. */
const listBlock = (n, startId = 1) => {
  const rows = Array.from({ length: n }, (_, i) =>
    `${i + 1}. [w-${startId + i}] 책 ${i + 1} | 저자 | 출판사 | 15,000원 | 무선제본(SEOJI확정) | ISBN: 978890000000${i % 10} | 신청자 테스트${(i % 7) + 1}(30세 남·성인, 이번 달 누계 1권) | 접수 2026-09-07 10:00`);
  return `[B-02 희망도서 주간 신청 목록 — 2026-09-07 ~ 2026-09-13 (9.7~9.13)]\n총 ${n}건 / 신청자 7명 · 제본형태 SEOJI 확정 ${n}건\n\n${rows.join("\n")}`;
};
const msgsWith = (block) => [{ role: "user", content: `화요일 처리 시작할게요.\n\n${block}` }];
const verdictBlock = (lines) => `판정했습니다.\n\n===판정시작===\n${lines.join("\n")}\n===판정끝===\n\n이상입니다.`;

// ---------------------------------------------------------------------------
// 판정값 정규화
// ---------------------------------------------------------------------------

test("판정 표기 흔들림을 네 갈래로 모은다", () => {
  for (const v of ["구입", "구입 대상", "통과", "승인", "적합"]) assert.equal(b02NormalizeVerdict(v), "구입");
  for (const v of ["반려", "부적합", "제외"]) assert.equal(b02NormalizeVerdict(v), "반려");
  for (const v of ["수동", "수동 검토", "MANUAL_REVIEW", "**MANUAL_REVIEW**", "검토"]) assert.equal(b02NormalizeVerdict(v), "수동");
  for (const v of ["보류", "대기"]) assert.equal(b02NormalizeVerdict(v), "보류");
});

test("모르는 판정값은 조용히 어느 갈래에도 넣지 않는다", () => {
  for (const v of ["", "글쎄요", "아마도 구입", undefined]) assert.equal(b02NormalizeVerdict(v), null);
});

// ---------------------------------------------------------------------------
// 신청 목록 되읽기
// ---------------------------------------------------------------------------

test("주입된 목록에서 식별자와 총계를 되읽는다", () => {
  const r = extractB02Requests(msgsWith(listBlock(25)));
  assert.equal(r.ids.size, 25);
  assert.ok(r.ids.has("w-1") && r.ids.has("w-25"));
  assert.deepEqual(r.headerTotal, { 신청: 25, 신청자: 7 });
  assert.equal(r.patrons.size, 7);
});

test("목록 블록이 없는 대화에서는 빈 기준을 돌려준다", () => {
  const r = extractB02Requests([{ role: "user", content: "안녕하세요" }]);
  assert.equal(r.ids.size, 0);
  assert.equal(r.headerTotal, null);
});

// ---------------------------------------------------------------------------
// 집계
// ---------------------------------------------------------------------------

test("판정 블록이 없으면 원문을 그대로 둔다", () => {
  const text = "이번 주 신청 건을 접수했습니다.";
  assert.equal(summarizeB02Verdicts(text, extractB02Requests(msgsWith(listBlock(3)))), text);
});

test("건별 판정을 세어 집계표를 붙이고 판정 블록은 지운다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-2|반려|R-02 수험서", "w-3|수동|R-06 확인"]),
    extractB02Requests(msgsWith(listBlock(3))));
  assert.ok(!out.includes("===판정시작==="), "판정 블록이 화면에 남았다");
  assert.match(out, /구입 대상: 1건/);
  assert.match(out, /반려: 1건/);
  assert.match(out, /수동 검토\(MANUAL_REVIEW\): 1건/);
  assert.match(out, /판정 합계: 3건/);
  assert.match(out, /총 신청: 3건 \/ 신청자 7명/);
  assert.ok(!out.includes("⚠ 확인 필요"), "정상인데 경고가 붙었다");
});

test("실측 사례를 재현한다 — 구입 8 / 반려 9 / 수동 8", () => {
  // 모델은 요약에 "반려 10 / 수동 7" 이라 썼지만 실제 판정은 9 / 8 이었다.
  const lines = [
    ...Array.from({ length: 8 }, (_, i) => `w-${i + 1}|구입|`),
    ...Array.from({ length: 9 }, (_, i) => `w-${i + 9}|반려|R-09 한도초과`),
    ...Array.from({ length: 8 }, (_, i) => `w-${i + 18}|수동|R-10 확인`),
  ];
  const out = summarizeB02Verdicts(verdictBlock(lines), extractB02Requests(msgsWith(listBlock(25))));
  assert.match(out, /구입 대상: 8건/);
  assert.match(out, /반려: 9건/);
  assert.match(out, /수동 검토\(MANUAL_REVIEW\): 8건/);
  assert.match(out, /판정 합계: 25건/);
  assert.ok(!out.includes("⚠ 확인 필요"));
});

test("반려 사유를 R-코드별로 쪼개 센다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|반려|R-02 수험서", "w-2|반려|R-02 자격증", "w-3|반려|R-09 한도초과", "w-4|구입|"]),
    extractB02Requests(msgsWith(listBlock(4))));
  assert.match(out, /R-02 2/);
  assert.match(out, /R-09 1/);
});

test("한 건에 코드가 여러 개면 맨 앞 코드로만 센다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|반려|R-02 수험서 + R-09 한도초과"]),
    extractB02Requests(msgsWith(listBlock(1))));
  assert.match(out, /R-02 1/);
  assert.ok(!/R-09 1/.test(out), "두 번 세었다");
});

// ---------------------------------------------------------------------------
// 교차 검증 — 모델이 목록과 어긋나게 답했을 때
// ---------------------------------------------------------------------------

test("판정을 빠뜨리면 어느 건인지 짚는다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-2|반려|R-02"]),
    extractB02Requests(msgsWith(listBlock(4))));
  assert.match(out, /⚠ 확인 필요/);
  assert.match(out, /판정 누락 2건/);
  assert.match(out, /w-3, w-4/);
  assert.match(out, /신청 4건 중 2건만 판정됨/);
});

test("목록에 없는 식별자를 지어내면 잡아낸다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-2|구입|", "w-999|구입|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.match(out, /목록에 없는 식별자 1건/);
  assert.match(out, /w-999/);
});

test("같은 건을 두 번 판정하면 한 번만 세고 알린다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-1|반려|R-02", "w-2|구입|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.match(out, /구입 대상: 2건/);
  assert.match(out, /반려: 0건/);
  assert.match(out, /중복 판정 1건/);
});

test("알 수 없는 판정값은 합계에 넣지 않고 따로 알린다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-2|글쎄요|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.match(out, /판정 합계: 1건/);
  assert.match(out, /판정값을 알 수 없는 행 1건/);
});

test("모델이 습관적으로 붙이는 표 헤더와 구분선은 무시한다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["식별자|판정|사유", "---|---|---", "w-1|구입|", "w-2|반려|R-02"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.match(out, /판정 합계: 2건/);
  assert.ok(!out.includes("⚠ 확인 필요"));
});

test("세로줄을 앞뒤로 두른 마크다운 표 행도 읽는다", () => {
  const out = summarizeB02Verdicts(
    verdictBlock(["| w-1 | 구입 | |", "| [w-2] | 반려 | R-02 수험서 |"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.match(out, /구입 대상: 1건/);
  assert.match(out, /반려: 1건/);
  assert.ok(!out.includes("⚠ 확인 필요"));
});

test("보류는 별도 줄로만 나오고 없으면 줄 자체가 없다", () => {
  const withHold = summarizeB02Verdicts(
    verdictBlock(["w-1|보류|R-01 B-03 회신 대기", "w-2|구입|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.match(withHold, /보류\(B-03 회신 대기\): 1건/);

  const noHold = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-2|구입|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.ok(!noHold.includes("보류"), "보류 0건인데 줄이 붙었다");
});

// ---------------------------------------------------------------------------
// 주차 표기 — 모델이 아니라 코드가 매긴다
// ---------------------------------------------------------------------------

const weekLabel = (() => {
  const mod2 = { exports: {} };
  new Function("module", "exports", grab("b02WeekLabel") + "\nmodule.exports = b02WeekLabel;")(mod2, mod2.exports);
  return mod2.exports;
})();

test("월을 넘나드는 주는 그 주 목요일이 속한 달을 따른다", () => {
  // 2026-08-31 ~ 09-06 은 목요일(09-03)이 9월이라 9월 1주차다.
  // 실측에서 모델은 09-07 주를 "9월 3주차"라 불렀지만 2주차가 맞다.
  assert.match(weekLabel("2026-08-31"), /2026년 9월 1주차/);
  assert.match(weekLabel("2026-09-07"), /2026년 9월 2주차/);
  assert.match(weekLabel("2026-09-14"), /2026년 9월 3주차/);
});

test("주차 표기에 실제 기간이 함께 붙는다", () => {
  assert.match(weekLabel("2026-09-07"), /9\.7~9\.13/);
  assert.match(weekLabel("2026-09-07"), /2026-09-07 ~ 2026-09-13/);
});

test("주차가 없거나 형식이 틀리면 원문을 돌려준다", () => {
  assert.equal(weekLabel(""), "");
  assert.equal(weekLabel(null), "");
  assert.equal(weekLabel("2026-13-99"), "2026-13-99");
});

// ---------------------------------------------------------------------------
// B-03 복본 인계 — 이 경로가 없으면 사서가 목록을 손으로 옮겨야 한다
// ---------------------------------------------------------------------------

test("신청 목록에서 저자·ISBN 까지 걷는다 (복본 검사에 넘길 값)", () => {
  const r = extractB02Requests(msgsWith(listBlock(3)));
  const bib = r.ids.get("w-2");
  assert.equal(bib.title, "책 2");
  assert.equal(bib.author, "저자");
  assert.match(bib.isbn, /^\d{13}$/);
});

test("구입·보류 건만 복본 검사 배치로 넘긴다", () => {
  resetBatch();
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-2|반려|R-02", "w-3|수동|R-06", "w-4|보류|R-01 대기"]),
    extractB02Requests(msgsWith(listBlock(4))));
  assert.ok(lastBatch, "배치가 등록되지 않았다");
  assert.equal(lastBatch.prefix, "B02");
  assert.deepEqual(lastBatch.items.map(i => i.wishlist_id), ["w-1", "w-4"]);
  assert.match(out, /복본 검사 배치 ID: `B02-20260912-1`/);
  assert.match(out, /\(2종\)/);
});

test("배치 항목에 B-03 조회에 필요한 서지가 실린다", () => {
  resetBatch();
  summarizeB02Verdicts(verdictBlock(["w-1|구입|", "w-2|구입|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  const it = lastBatch.items[0];
  assert.equal(it.candidate_id, "c-1");   // B-03 판정 결과가 행과 대응되도록 순번을 붙인다
  assert.equal(it.wishlist_id, "w-1");
  assert.equal(it.title, "책 1");
  assert.equal(it.author, "저자");
  assert.match(it.isbn, /^\d{13}$/);
});

test("넘길 건이 없으면 배치를 만들지 않는다", () => {
  resetBatch();
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|반려|R-02", "w-2|수동|R-06"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.equal(lastBatch, null, "넘길 게 없는데 빈 배치를 만들었다");
  assert.ok(!out.includes("복본 검사 배치 ID"));
});

test("판정 블록이 없는 턴에는 배치를 만들지 않는다", () => {
  resetBatch();
  summarizeB02Verdicts("접수만 했습니다.", extractB02Requests(msgsWith(listBlock(3))));
  assert.equal(lastBatch, null);
});

test("목록에 없는 식별자는 배치에 넣지 않는다", () => {
  resetBatch();
  const out = summarizeB02Verdicts(
    verdictBlock(["w-1|구입|", "w-999|구입|"]),
    extractB02Requests(msgsWith(listBlock(2))));
  assert.deepEqual(lastBatch.items.map(i => i.wishlist_id), ["w-1"]);
  assert.match(out, /목록에 없는 식별자 1건/);   // 배치에서 빠진 사실이 경고로도 드러난다
});
