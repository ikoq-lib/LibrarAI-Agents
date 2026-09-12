// 문서화 패스 유틸 검증 — LibrarAI.html 의 번들러 구간을 그대로 꺼내 돌린다(설계 6.2·7절).
// 브라우저 API(JSZip·XLSX·Blob)가 필요한 부분은 제외하고 순수 함수만 본다.
//
// 실행: node scripts/test-doc-pass.mjs
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestSrc = fs.readFileSync(path.join(root, "doc_manifest_data.js"), "utf8");
const html = fs.readFileSync(path.join(root, "LibrarAI.html"), "utf8");

const slice = (from, to) => {
  const a = html.indexOf(from), b = html.indexOf(to);
  if (a < 0 || b < 0) { console.error(`구간을 찾지 못했습니다: ${from}`); process.exit(1); }
  return html.slice(a, b);
};
const helpers = slice("    // ── 문서 매니페스트 헬퍼", "    const isoWeekInfo =");
const bundler = slice("    // ── 문서 번들러 (설계 7절", "    // ── TabbedDocument");
const parser = slice("    const DOC_BLOCK_SPECS = [", "    // 레버4 — 동시 in-flight");

const api = new Function(`
  const fmtStamp = (v) => "2026. 9. 3. 14:20";
  const loadJSZip = () => { throw new Error("browser only"); };
  const loadXLSX = () => { throw new Error("browser only"); };
  const parseMarkdownTableRows = () => [];
  const buildHwpxSection0 = (t) => t;
  const base64ToUint8Array = () => new Uint8Array();
  const HWPX_BASE_TEMPLATE_B64 = "";
  const Blob = function () {};
  const URL = { createObjectURL: () => "", revokeObjectURL: () => {} };
  const document = { createElement: () => ({ click() {}, remove() {} }), body: { appendChild() {} } };
  ${manifestSrc}
  ${helpers}
  ${parser}
  ${bundler}
  return { buildDocUserMessage, docBasisText, safeFilename, parseDocBlocks, BUNDLE_GROUP_ORDER,
           parseTargetPeriod, buildDocChecklist, approvalLineFor, DOC_SKELETONS };
`)();

let failures = 0;
const check = (label, cond, detail = "") => {
  console.log(`  ${cond ? "[ok ]" : "[FAIL]"} ${label}${cond ? "" : ` — ${detail}`}`);
  if (!cond) failures++;
};

// ── 확정본 stub — 리프 원문이 보존된 run
const run = {
  target_period: "2026-09",
  confirmed: {
    seq: 1, at: Date.now(),
    reportText: "# 2026년 9월 업무계획\n희망도서 구입과 장서현황 보고를 진행한다.",
    dispatches: [{
      agent: "dm01-collection-domain",
      resultText: "DM-01 취합 본문",
      leafSteps: [{ agentId: "b02-wishlist", status: "done", text: "B-02 희망도서 리프 산출물 원문 — 36건, 72만원" }],
    }],
  },
};
const { items } = api.buildDocChecklist(run, {});
const period = api.parseTargetPeriod(run.target_period);
const wish = items.find(i => i.tpl === "TPL-014");
const wishXlsx = items.find(i => i.tpl === "ATT-007");
const news = items.find(i => i.tpl === "TPL-031");

console.log("[문서 생성 요청 메시지 — 희망도서 구입 건의]");
const msg = api.buildDocUserMessage(wish, run, period);
console.log(msg.split("\n").slice(0, 8).map(l => "    " + l).join("\n"));

check("대상 기간·확정 차수 표기", msg.includes("2026년 9월 (1차 확정본"), msg.slice(0, 80));
check("양식 번호 전달", msg.includes("양식: TPL-014"));
check("출력 블록 지정(기안문)", msg.includes("===기안문시작==="));
check("결재선 주입(자료개발 2단)", msg.includes("결재선: 주무관 · 도서관장"));
check("문서 골격 주입", msg.includes("[문서 골격]") && msg.includes("수신  내부결재"));
check("확정본 근거로 리프 원문 사용", msg.includes("B-02 희망도서 리프 산출물 원문"));

const msgXlsx = api.buildDocUserMessage(wishXlsx, run, period);
check("붙임 xlsx는 엑셀 블록 지정", msgXlsx.includes("===엑셀시작==="));

const msgNews = api.buildDocUserMessage(news, run, period);
check("소식지는 대외발송 골격", msgNews.includes("수신  수신자 참조") && msgNews.includes("경상남도교육청 창녕도서관장"));
check("소식지 통권 제목 치환", news.title.includes("통권 제138호"), news.title);

// 근거 폴백 순서 — 리프 원문 → 같은 도메인 취합본 → 확정본 전문
const sameDomain = { ...wish, leaf: "b06-inspection" };
check("리프 원문이 없으면 같은 도메인 취합본",
  api.buildDocUserMessage(sameDomain, run, period).includes("DM-01 취합 본문"));

const otherDomain = { ...wish, leaf: "f04-newsletter", group: "dm05-pr-partnership-domain" };
check("도메인 근거도 없으면 확정본 전문 폴백",
  api.buildDocUserMessage(otherDomain, run, period).includes("2026년 9월 업무계획"));

// ── 블록 파싱(R-6)
const reply = "설명\n===기안문시작===\n본문A\n===기안문끝===\n===엑셀시작===\n| a | b |\n===엑셀끝===";
const blocks = api.parseDocBlocks(reply);
check("블록 2개 등장 순서 유지", blocks.length === 2 && blocks[0].kind === "기안문" && blocks[1].kind === "엑셀");
check("블록 없는 응답은 빈 배열", api.parseDocBlocks("블록 없는 텍스트").length === 0);

// ── 파일명·폴더 규칙(7.4)
check("금지문자 제거·공백 밑줄", api.safeFilename('9월 희망/도서: 구입*건의') === "9월_희망도서_구입건의",
  api.safeFilename('9월 희망/도서: 구입*건의'));
check("40자 절단", api.safeFilename("가".repeat(60)).length === 40);
check("빈 값은 폴백", api.safeFilename("   ", "문서") === "문서");
check("도메인 폴더 순번", api.BUNDLE_GROUP_ORDER["dm01-collection-domain"] === "01_DM-01_장서");
check("chief 폴더", api.BUNDLE_GROUP_ORDER["chief"] === "09_기획담당");

// ── 결재선 분기(8.3)
check("웹툰 결재선 예외", api.approvalLineFor("TPL-020") === "사서팀장 · 도서관장");
check("강사비 결재선", api.approvalLineFor("TPL-027") === "행정실장");
check("기본 결재선", api.approvalLineFor(null) === "주무관 · 사서팀장 · 도서관장");

// ── 골격 4종
check("골격 4종 등록", Object.keys(api.DOC_SKELETONS).length === 4, Object.keys(api.DOC_SKELETONS).join(","));

console.log(failures ? `\n실패 ${failures}건` : "\n전체 통과");
process.exit(failures ? 1 : 0);
