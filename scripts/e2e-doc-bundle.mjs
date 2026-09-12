// 문서번들 5단계 실사용 테스트 — 9월 확정본에서 실제 문서를 생성하고 zip까지 받아본다.
//
// 전제: node scripts/dev-server.mjs 가 떠 있어야 한다(실제 /api/chat 호출).
// 확정본은 테스트 픽스처다 — chief 전체 사이클을 다시 돌리지 않고, 확정 스냅샷만 주입해
// 문서화 패스·번들러 경로를 검증한다.
//
// 실행: node scripts/e2e-doc-bundle.mjs [--limit N] [--port 5173]
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const argv = process.argv.slice(2);
const arg = (name, dflt) => {
  const i = argv.indexOf(name);
  return i >= 0 ? argv[i + 1] : dflt;
};
const port = +arg("--port", 5173);
const limit = +arg("--limit", 0);          // 0 = 전체
const outDir = path.join(root, ".artifacts", "e2e-doc-bundle");
fs.mkdirSync(outDir, { recursive: true });

// ── 9월 확정본 픽스처 ────────────────────────────────────────────
const leaf = (agentId, text) => ({ agentId, status: "done", summary: text.slice(0, 60), text });
const REPORT = `# 2026년 9월 도서관 월간 업무계획

## 1. 총괄 요약
- 희망도서 36건(72만원)을 구입 건의하고, 8월 장서현황을 보고한다.
- 10월 독서진흥행사 계획과 8월 결과를 함께 처리한다.
- 소식지 「우포」 9월호(통권 138호)와 보도자료를 배포한다.
- 하반기 평생학습 5개 강좌의 9월 강사비를 지급한다.

## 2. 도메인별 상세
### DM-01 장서
희망도서 36건 · 소요 720,000원 · 예산과목 자료구입비. 장서현황 73,390책.

### DM-03 독서문화
10월 독서진흥행사 3종(가을 독서한마당·시 낭송회·북스타트), 8월 행사 결과 2종.

### DM-04 평생학습
하반기 5개 강좌 운영 중. 9월 강사비 150만원(50,000원×2시간×15회).

### DM-05 홍보협력
소식지 9월호 배부, 보도자료 1건(하반기 평생학습 수강생 모집).
`;

const WRAPPED = `===보고서시작===\n${REPORT}\n===보고서끝===`;
const FIXTURE_RUN_ID = "run_1788000000000";
const fixture = {
  chiefMsgs: [
    { role: "assistant", content: "안녕하세요! 업무 총괄 에이전트입니다." },
    { role: "user", content: "9월 업무 계획 제출해줘" },
    { role: "assistant", kind: "report", runId: FIXTURE_RUN_ID,
      content: `9월 계획을 정리했습니다.\n\n${WRAPPED}` },
  ],
  chiefRuns: {
    [FIXTURE_RUN_ID]: {
      status: "done", scope: "monthly", target_period: "2026-09",
      // 확정 스냅샷의 reportText 는 구분자를 포함한 전문이다(renderReport 결과와 같은 모양).
      reportSkeleton: WRAPPED, resultText: WRAPPED,
      stage: "confirmed",
      confirmed: {
        at: new Date("2026-09-03T14:20:00+09:00").toISOString(), seq: 1, reportText: WRAPPED,
        dispatches: [
          { agent: "dm01-collection-domain", status: "done", resultText: "DM-01 장서 도메인 9월 취합",
            leafSteps: [
              leaf("b02-wishlist", "[B-02 희망도서] 9월 신청 36건 접수, 승인 36건. 총 720,000원. 제외 0건. 예산과목: 자료구입비. 관련 문서: 창녕도서관-1204(2026. 8. 28., 「2026년 자료 확충 계획」)"),
              leaf("b05-balance", "[B-05 장서균형] 2026년 8월 말 기준 총 장서 73,390책. KDC 8류 21.4%, 3류 12.8%, 9류 9.1%. 목표 대비 8류 과다·5류 부족. 자료실별: 종합 48,210 / 어린이 19,880 / 유아 5,300"),
            ] },
          { agent: "dm03-reading-culture-domain", status: "done", resultText: "DM-03 독서문화 9월 취합",
            leafSteps: [
              leaf("planner", "[D-02 행사기획] 10월 독서진흥행사 3종 — ①가을 독서한마당(10.11.~10.12., 도서관 마당, 전 연령, 예산 80만원) ②시 낭송회(10.18. 14:00, 강의실1, 성인 20명, 30만원) ③북스타트 그림책놀이(10.25. 10:00, 강의실2, 유아 10명, 20만원). 8월 결과 — 여름 독서캠프 참여 64명(만족도 4.6), 광복절 특별전 관람 320명. 북큐레이션 10월 주제 '깊어가는 가을, 시를 읽다'."),
            ] },
          { agent: "dm04-lifelong-learning-domain", status: "done", resultText: "DM-04 평생학습 9월 취합",
            leafSteps: [
              leaf("ll-operation-log", "[E-04 운영일지] 하반기 5개 강좌 9월 강사비 — 스마트폰 활용교실 3회 30만원 / 감성 캘리그라피 3회 30만원 / 그림책 만들기 2회 20만원 / 힐링 오일파스텔 3회 30만원 / 칼림바 첫걸음 4회 40만원. 합계 1,500,000원(50,000원×2시간 기준). 예산과목: 평생학습 강사수당."),
            ] },
          { agent: "dm05-pr-partnership-domain", status: "done", resultText: "DM-05 홍보협력 9월 취합",
            leafSteps: [
              leaf("f04-newsletter", "[F-04 소식지] 「우포」 9월호(통권 제138호) 배부 예정. 수록 — 독서진흥행사(여름 독서캠프 결과·10월 예고), 하반기 평생학습 5강좌 안내, 공연 '가을밤 작은음악회'(9.26. 19:00), 체험 '책갈피 만들기', 북큐레이션 '깊어가는 가을, 시를 읽다', 이용안내(평일 09:00~18:00, 주말 09:00~17:00, 월요일·법정공휴일 휴관, ☎055-530-1234). 보도자료 1건 — 하반기 평생학습 수강생 모집(9.15.~9.25. 접수, 무료)."),
            ] },
        ],
      },
      dispatches: [],
    },
  },
};

const browser = await chromium.launch();
const context = await browser.newContext({ acceptDownloads: true });
const page = await context.newPage();
const pageErrors = [];
page.on("pageerror", e => pageErrors.push(e.message));
page.on("console", m => { if (m.type() === "error") pageErrors.push("console: " + m.text()); });

const base = `http://localhost:${port}/`;
await page.goto(base);
await page.evaluate((state) => localStorage.setItem("librarai_chief_state", JSON.stringify(state)), fixture);
await page.reload();
await page.waitForTimeout(3000);

// 확정 배지와 📦 버튼 확인
const bundleBtn = page.getByRole("button", { name: /실행 문서 생성/ });
await bundleBtn.waitFor({ timeout: 15000 });
console.log("① 확정본 렌더 + 📦 버튼 노출 OK");
await bundleBtn.click();
await page.waitForTimeout(800);

const header = await page.locator("text=/실행 문서 .*건 예정/").first().innerText();
console.log("② 생성 목록:", header.replace(/\s+/g, " ").trim());
await page.screenshot({ path: path.join(outDir, "01_checklist.png"), fullPage: false });

// --limit 이 있으면 앞의 N건만 남기고 체크 해제
if (limit) {
  const boxes = page.locator('input[type="checkbox"]');
  const total = await boxes.count();
  for (let i = limit; i < total; i++) {
    const box = boxes.nth(i);
    if (await box.isEnabled() && await box.isChecked()) await box.uncheck();
  }
  console.log(`   (--limit ${limit} — 앞 ${limit}건만 생성)`);
}

const startBtn = page.getByRole("button", { name: /문서 생성 시작/ });
await startBtn.click();
console.log("③ 생성 시작 — 진행 상황:");

const deadline = Date.now() + 20 * 60 * 1000;
let last = "";
while (Date.now() < deadline) {
  const done = await page.locator("text=/^완료$/").count();
  const err = await page.locator("text=/^실패$/").count();
  const running = await page.locator("text=/^진행$/").count();
  const waiting = await page.locator("text=/^대기$/").count();
  const line = `   완료 ${done} · 진행 ${running} · 대기 ${waiting} · 실패 ${err}`;
  if (line !== last) { console.log(line); last = line; }
  if (!running && !waiting) break;
  await page.waitForTimeout(5000);
}

await page.screenshot({ path: path.join(outDir, "02_progress.png"), fullPage: false });

// 결과 표 — 문서별 상태와 오류
const rows = await page.evaluate(() => {
  const out = [];
  document.querySelectorAll("div").forEach(() => {});
  return out;
});

const zipBtn = page.getByRole("button", { name: /전체 zip 다운로드/ });
let zipInfo = "없음";
if (await zipBtn.count()) {
  const [download] = await Promise.all([
    page.waitForEvent("download", { timeout: 120000 }),
    zipBtn.click(),
  ]);
  const target = path.join(outDir, download.suggestedFilename());
  await download.saveAs(target);
  zipInfo = `${download.suggestedFilename()} (${(fs.statSync(target).size / 1024).toFixed(1)} KB)`;
  console.log("④ zip 저장:", zipInfo);
} else {
  console.log("④ zip 버튼이 없습니다 — 완료 건이 0건입니다.");
}

const summary = await page.locator("text=/완료 \\d+건/").last().innerText().catch(() => "");
console.log("⑤ 요약:", summary.replace(/\s+/g, " ").trim());
if (pageErrors.length) {
  console.log("⚠ 페이지 오류", pageErrors.length, "건");
  pageErrors.slice(0, 5).forEach(e => console.log("   ", e.slice(0, 160)));
}

await browser.close();
console.log("\n산출물:", outDir);
