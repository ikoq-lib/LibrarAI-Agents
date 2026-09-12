// zip 번들 생성 검증 — JSZip·XLSX가 필요해 헤드리스 브라우저에서 돌린다(설계 7.2·7.3).
// LibrarAI.html 을 연 뒤 번들러 구간을 페이지 안에서 평가해 실제 zip 을 만들어 본다.
//
// 실행: node scripts/test-doc-bundle-zip.mjs
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const html = fs.readFileSync(path.join(root, "LibrarAI.html"), "utf8");
const slice = (from, to) => html.slice(html.indexOf(from), html.indexOf(to));
const helpers = slice("    // ── 문서 매니페스트 헬퍼", "    const isoWeekInfo =");
const bundler = slice("    // ── 문서 번들러 (설계 7절", "    // ── TabbedDocument");
// 번들러가 쓰는 하위 유틸(hwpx 섹션 조립·base64·표 파서·CDN 로더)은 페이지에 이미 있지만
// 클로저 안이라 꺼낼 수 없다. 선언 단위로 뽑아 페이지 전역에서 다시 만든다.
// 선언 하나를 통째로 뽑는다. 본문이 있으면 중괄호 짝을 세어 끝을 찾고,
// 표현식 화살표 함수면 첫 세미콜론까지다(문자열 안의 괄호·세미콜론은 건너뛴다).
const grab = (decl) => {
  const start = html.indexOf(decl);
  if (start < 0) { console.error("선언을 찾지 못했습니다: " + decl); process.exit(1); }
  let depth = 0, quote = "", opened = false;
  for (let i = start; i < html.length; i++) {
    const ch = html[i], prev = html[i - 1];
    if (quote) { if (ch === quote && prev !== "\\") quote = ""; continue; }
    if (ch === '"' || ch === "'" || ch === "`") { quote = ch; continue; }
    if (ch === "/" && html[i + 1] === "/") { i = html.indexOf("\n", i); continue; }
    if (ch === "{") { depth++; opened = true; }
    else if (ch === "}") { depth--; if (opened && depth === 0) return html.slice(start, html.indexOf(";", i) + 1) + "\n"; }
    else if (ch === ";" && !opened && depth === 0) return html.slice(start, i + 1) + "\n";
  }
  console.error("선언의 끝을 찾지 못했습니다: " + decl);
  process.exit(1);
};
const support = [
  "    const parseMarkdownTableRows = (tableLines) =>",
  "    const loadXLSX = () => {",
  "    let _jszipLoadPromise = null;",
  "    const loadJSZip = () => {",
  "    const buildHwpxSection0 = (bodyText) => {",
  "    const base64ToUint8Array = (b64) => {",
].map(grab).join("\n")
  + "\n" + slice("    const HWPX_SECTION_HEADER", "    const buildHwpxSection0");

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on("pageerror", e => errors.push(e.message));
await page.goto("file:///" + path.posix.join(root, "LibrarAI.html"));
await page.waitForTimeout(2500);

const result = await page.evaluate(async ({ helpers, bundler, support }) => {
  const make = new Function(`
    const fmtStamp = () => "2026. 9. 3. 14:20";
    ${support}
    ${helpers}
    ${bundler}
    return { buildBundleZip, buildHwpxBlob, buildXlsxBlob, safeFilename };
  `);
  const api = make();
  const run = { target_period: "2026-09", confirmed: { seq: 1, at: Date.now(), reportText: "# 9월 업무계획\\n본문" } };
  const items = [
    { key: "a", group: "dm01-collection-domain", leaf: "b02-wishlist", tpl: "TPL-014", kind: "기안문",
      format: "hwpx", title: "9월 희망도서 구입 건의", status: "done", body: "제목  9월 희망도서 구입 건의\\n\\n본문" },
    { key: "b", group: "dm01-collection-domain", leaf: "b02-wishlist", tpl: "ATT-007", kind: "붙임",
      format: "xlsx", title: "9월 희망도서 구입 목록", status: "done", body: "| 서명 | 저자 |\\n|---|---|\\n| 책 | 저자 |" },
    { key: "c", group: "chief", leaf: null, tpl: null, kind: "기안문", format: "hwpx",
      title: "9월 이용 실적 보고", status: "error", error: "블록 없음" },
  ];
  const blob = await api.buildBundleZip(run, items, run.confirmed.reportText);
  const JSZipLib = await loadJSZipGlobal();
  const zip = await JSZipLib.loadAsync(blob);
  const names = Object.keys(zip.files).filter(n => !zip.files[n].dir);
  const listing = await zip.file("_생성목록.md").async("string");
  return { size: blob.size, names, listing };

  function loadJSZipGlobal() { return Promise.resolve(window.JSZip); }
}, { helpers, bundler, support });

let failures = 0;
const check = (label, cond, detail = "") => {
  console.log(`  ${cond ? "[ok ]" : "[FAIL]"} ${label}${cond ? "" : ` — ${detail}`}`);
  if (!cond) failures++;
};

console.log(`zip ${(result.size / 1024).toFixed(1)} KB · 파일 ${result.names.length}개`);
result.names.forEach(n => console.log("    " + n));

check("통합계획서 포함", result.names.some(n => n.startsWith("00_통합계획서/")));
check("도메인 폴더 구조", result.names.some(n => n.startsWith("01_DM-01_장서/b02-wishlist/")));
check("기안문 hwpx", result.names.some(n => n.endsWith("(기안문).hwpx")));
check("붙임 xlsx", result.names.some(n => n.endsWith("(붙임).xlsx")));
check("순번 접두", result.names.some(n => /\/0\d_/.test(n)));
check("_생성목록.md 포함", result.names.includes("_생성목록.md"));
check("실패 건은 파일 없이 목록에만", !result.names.some(n => n.includes("이용_실적")) && result.listing.includes("실패: 블록 없음"));
check("양식 미등록 경고", result.listing.includes("양식 미등록"));
check("확정 차수 기록", result.listing.includes("확정 차수: 1차"));
check("AI 초안 고지", result.listing.includes("AI 생성 초안"));
check("페이지 오류 없음", errors.length === 0, errors[0]);

await browser.close();
console.log(failures ? `\n실패 ${failures}건` : "\n전체 통과");
process.exit(failures ? 1 : 0);
