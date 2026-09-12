// 생성 목록 계산 검증 — LibrarAI.html 안의 헬퍼를 그대로 꺼내 돌린다.
// 규칙을 다시 구현하지 않는다. 설계 5.6의 2026년 9월 예시와 대조한다.
//
// 실행: node scripts/test-doc-checklist.mjs
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestSrc = fs.readFileSync(path.join(root, "doc_manifest_data.js"), "utf8");
const html = fs.readFileSync(path.join(root, "LibrarAI.html"), "utf8");

const begin = html.indexOf("    // ── 문서 매니페스트 헬퍼");
const end = html.indexOf("    const isoWeekInfo =");
if (begin < 0 || end < 0) {
  console.error("헬퍼 구간을 찾지 못했습니다 — LibrarAI.html 의 마커가 바뀌었는지 확인하세요.");
  process.exit(1);
}
const helpers = html.slice(begin, end);

const sandbox = new Function(`
  ${manifestSrc}
  ${helpers}
  return { buildDocChecklist, parseTargetPeriod, weeksInMonth, manualDocRows, newsletterIssue };
`)();

let failures = 0;
const check = (label, actual, expected) => {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  console.log(`  ${ok ? "[ok ]" : "[FAIL]"} ${label}: ${JSON.stringify(actual)}${ok ? "" : ` (기대 ${JSON.stringify(expected)})`}`);
  if (!ok) failures++;
};

// 설계 5.6 — 2026년 9월(분기 실행월 아님, 하반기 평생학습 운영 중, 조건부 없음)
// 조건부 키워드가 들어가지 않도록 중립적인 본문을 쓴다("강사비"가 있으면 강사 조건이 붙는다).
const run = {
  target_period: "2026-09",
  confirmed: { reportText: "9월 업무계획. 희망도서 구입, 장서현황 보고, 독서진흥행사, 소식지와 보도자료 배포를 진행한다." },
};
const { items, period } = sandbox.buildDocChecklist(run, {});
const buildable = items.filter(i => i.format !== "none");
const hwpx = buildable.filter(i => i.format === "hwpx").length;
const xlsx = buildable.filter(i => i.format === "xlsx").length;

console.log(`2026년 ${period.month}월 생성 목록 — 총 ${buildable.length}건 (hwpx ${hwpx} · xlsx ${xlsx})`);
buildable.forEach(i => console.log(`    · ${i.title} [${i.kind}·${i.format}·${i.tpl || "양식 미등록"}] ${i.leaf || "chief"}`));

// 설계 5.6은 hwpx 11 · xlsx 4 = 15건이었다. 지금은 16건이며 차이는 1건뿐이다 —
// 소식지 본체 원고(ATT-015). 설계 당시에는 소식지 본체를 디자인 편집물로 보고 format:none
// 이었으나, 2026-09-03 A-01 카탈로그가 ATT-015를 "원고 텍스트만 생성"으로 등록했다.
// 4쪽 디자인은 여전히 사람이 입힌다.
check("9월 hwpx 건수", hwpx, 12);
check("9월 xlsx 건수", xlsx, 4);
check("9월 합계", buildable.length, 16);
check("소식지 통권(2026-09)", sandbox.newsletterIssue(2026, 9), 138);
check("소식지 통권(2026-12)", sandbox.newsletterIssue(2026, 12), 141);
check("주 수(2026-09)", sandbox.weeksInMonth(2026, 9), 4);
check("manual 행 수", sandbox.manualDocRows().length, 3);

// 분기 실행월(8월)에는 정기도서수서가 붙는다
const aug = sandbox.buildDocChecklist({ target_period: "2026-08", confirmed: { reportText: "8월 정기도서수서 진행" } }, {});
check("8월에 정기도서수서 포함", aug.items.some(i => i.taskName === "정기도서수서"), true);
check("9월에 정기도서수서 없음", items.some(i => i.taskName === "정기도서수서"), false);

// 조건부 — 강사 키워드가 있으면 범죄경력조회가 붙는다(설계 5.4)
const withTeacher = sandbox.buildDocChecklist(
  { target_period: "2026-09", confirmed: { reportText: "9월 독서진흥행사에 외부 강사를 섭외하고 강사비를 지급한다." } }, {});
check("강사 키워드로 범죄경력조회 노출",
  withTeacher.items.some(i => i.condition === "강사 있음"), true);
check("강사 조건 포함 시 17건",
  withTeacher.items.filter(i => i.format !== "none").length, 17);

// 조건부 — 확정본에 "웹툰"이 있으면 후보로 잡힌다
const webtoon = sandbox.buildDocChecklist({ target_period: "2026-08", confirmed: { reportText: "8월 정기도서수서. 웹툰 자료 포함." } }, {});
check("웹툰 키워드로 조건부 문서 노출", webtoon.items.some(i => i.condition === "웹툰도서 포함"), true);

// manual 수량 입력 — 독서동아리 2개면 문서가 2배
const clubs = sandbox.buildDocChecklist(run, { "독서동아리 운영#10": 2 });
const clubDocs = clubs.items.filter(i => i.taskName === "독서동아리 운영").length;
check("독서동아리 2개 입력 시 문서 14건", clubDocs, 14);

console.log(failures ? `\n실패 ${failures}건` : "\n전체 통과");
process.exit(failures ? 1 : 0);
