// 총괄 지시 대화 세션 검증 — 새 대화 / 이전 대화 전환 / 확정본 보존.
// LLM 호출 없이 UI 동작만 본다(대화는 localStorage 에 주입).
//
// 전제: node scripts/dev-server.mjs
// 실행: node scripts/test-chief-sessions.mjs [--port 5173]
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const i = process.argv.indexOf("--port");
const port = +(i >= 0 ? process.argv[i + 1] : 5173);

const REPORT = "===보고서시작===\n# 2026년 9월 업무계획\n희망도서 36건\n===보고서끝===";
const seeded = {
  chiefMsgs: [
    { role: "assistant", content: "안녕하세요! 업무 총괄 에이전트입니다." },
    { role: "user", content: "9월 업무 계획 제출해줘" },
    { role: "assistant", kind: "report", runId: "run_1", content: REPORT },
  ],
  chiefRuns: {
    run_1: {
      status: "done", scope: "monthly", target_period: "2026-09",
      reportSkeleton: REPORT, stage: "confirmed",
      confirmed: { at: new Date().toISOString(), seq: 1, reportText: REPORT, dispatches: [] },
      dispatches: [],
    },
  },
};

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", e => errors.push(e.message));
page.on("console", m => { if (m.type() === "error") errors.push("console: " + m.text().slice(0, 160)); });

let failures = 0;
const check = (label, cond, detail = "") => {
  console.log(`  ${cond ? "[ok ]" : "[FAIL]"} ${label}${cond ? "" : ` — ${detail}`}`);
  if (!cond) failures++;
};

await page.goto(`http://localhost:${port}/`);
await page.evaluate(s => localStorage.setItem("librarai_chief_state", JSON.stringify(s)), seeded);
await page.reload();
await page.waitForTimeout(3000);

const body = () => page.innerText("body");
check("대화 제목이 툴바에 뜬다", (await body()).includes("9월 업무 계획 제출해줘"));
check("확정본이 보인다", (await body()).includes("확정"));
check("처음에는 이전 대화 버튼이 없다", !(await page.getByRole("button", { name: /이전 대화/ }).count()));

// 새 대화
await page.getByRole("button", { name: /새 대화/ }).click();
await page.waitForTimeout(600);
const afterNew = await body();
check("새 대화 후 이전 메시지가 사라진다", !afterNew.includes("9월 업무 계획 제출해줘"));
check("새 대화 후 인사말만 남는다", afterNew.includes("무엇을 처리할까요"));
check("이전 대화 보관됨(1)", (await page.getByRole("button", { name: /이전 대화 1/ }).count()) === 1);

// 보관함 열고 되돌아가기
await page.getByRole("button", { name: /이전 대화 1/ }).click();
await page.waitForTimeout(400);
check("보관 목록에 제목이 보인다", (await body()).includes("9월 업무 계획 제출해줘"));
check("확정본 포함 표시", (await body()).includes("확정본 포함"));
await page.screenshot({ path: path.join(root, ".artifacts", "sessions_menu.png") });

await page.locator("text=9월 업무 계획 제출해줘").last().click();
await page.waitForTimeout(700);
const restored = await body();
check("이전 대화로 복원된다", restored.includes("9월 업무계획"));
check("복원 후 확정 상태 유지", restored.includes("확정"));
check("복원한 대화는 보관함에서 빠진다", !(await page.getByRole("button", { name: /이전 대화/ }).count()));

// 새로고침해도 유지되는가
await page.getByRole("button", { name: /새 대화/ }).click();
await page.waitForTimeout(500);
await page.reload();
await page.waitForTimeout(2500);
check("새로고침 후에도 보관함 유지", (await page.getByRole("button", { name: /이전 대화 1/ }).count()) === 1);

check("페이지 오류 없음", errors.length === 0, errors[0]);
await browser.close();
console.log(failures ? `\n실패 ${failures}건` : "\n전체 통과");
process.exit(failures ? 1 : 0);
