#!/usr/bin/env node
/**
 * OpenRouter Gemini: "그라운딩(네이티브 Google Search) + tools(function calling)"
 * 동시 호출 가능 여부 스모크테스트.
 *
 * 배경: B-01 수서 에이전트가 네이버 책 검색 API 종료에 대비해 Gemini 그라운딩으로
 * 인기/화제성 신호를 보강할지 검토 중. CHAT_MODELS에 넣는 모델은 chief ROUTE 위임을
 * 위해 tools를 지원해야 하므로, "한 요청 안에서 그라운딩과 사용자 정의 tools가 함께
 * 도는가"를 실제로 확인해야 한다. (과거 Gemini 1.5에선 google_search와 function
 * declaration을 같은 요청에 섞을 수 없었음.)
 *
 * 실행:
 *   OPENROUTER_API_KEY=sk-or-... node scripts/smoke-grounding-tools.mjs
 *   node scripts/smoke-grounding-tools.mjs --model google/gemini-3.5-flash
 *
 * 키는 환경변수 OPENROUTER_API_KEY 우선, 없으면 ./.env.local → ../.env.local 에서 로드.
 * 주의: 네이티브 그라운딩은 Google 요율이 패스스루로 과금됩니다(응답당 여러 검색
 *       쿼리가 발생할 수 있음). 이 스크립트는 최대 4~5회 호출합니다.
 */

import fs from "node:fs";
import path from "node:path";

// ── 설정 ──────────────────────────────────────────────────────────
const ARGV = process.argv.slice(2);
const argModel = (() => {
  const i = ARGV.indexOf("--model");
  return i >= 0 ? ARGV[i + 1] : null;
})();
const MODEL = argModel || process.env.SMOKE_MODEL || "google/gemini-3.5-flash";
const BASE = "https://openrouter.ai/api/v1";

// ── .env.local 최소 파서 (의존성 없음) ────────────────────────────
function loadEnvKey(name) {
  if (process.env[name]) return process.env[name];
  for (const p of [".env.local", "../.env.local"]) {
    try {
      const abs = path.resolve(process.cwd(), p);
      if (!fs.existsSync(abs)) continue;
      for (const line of fs.readFileSync(abs, "utf8").split("\n")) {
        const m = line.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/);
        if (m && m[1] === name) {
          return m[2].replace(/^["']|["']$/g, "").trim();
        }
      }
    } catch { /* ignore */ }
  }
  return null;
}

const API_KEY = loadEnvKey("OPENROUTER_API_KEY");
if (!API_KEY) {
  console.error(
    "\n✖ OPENROUTER_API_KEY 를 찾을 수 없습니다.\n" +
    "  이 키는 이 저장소 로컬 .env.local 에 없고 Vercel 서버 환경변수에만 있습니다.\n" +
    "  실행 예: OPENROUTER_API_KEY=sk-or-... node scripts/smoke-grounding-tools.mjs\n"
  );
  process.exit(2);
}

// ── 공용 헬퍼 ─────────────────────────────────────────────────────
const HEADERS = {
  "Authorization": `Bearer ${API_KEY}`,
  "Content-Type": "application/json",
  "HTTP-Referer": "https://librarai.local/smoke-test",
  "X-Title": "LibrarAI grounding+tools smoke test",
};

async function callOR(body) {
  const started = Date.now();
  let res, text;
  try {
    res = await fetch(`${BASE}/chat/completions`, {
      method: "POST",
      headers: HEADERS,
      body: JSON.stringify(body),
    });
    text = await res.text();
  } catch (e) {
    return { ok: false, status: 0, ms: Date.now() - started, error: `network: ${e.message}` };
  }
  let json = null;
  try { json = JSON.parse(text); } catch { /* keep raw */ }
  return { ok: res.ok, status: res.status, ms: Date.now() - started, json, raw: text };
}

// 도서관 소장 조회 도구(B-01 맥락) — 실제 실행하지 않고 호출 발생 여부만 본다.
const CATALOG_TOOL = {
  type: "function",
  function: {
    name: "search_library_catalog",
    description: "우리 도서관 소장 목록에서 제목/저자로 도서를 조회한다. 소장 여부·청구기호·대출가능 여부를 반환한다.",
    parameters: {
      type: "object",
      properties: {
        title: { type: "string", description: "도서 제목" },
        author: { type: "string", description: "저자명(선택)" },
      },
      required: ["title"],
    },
  },
};

const NATIVE_WEB = [{ id: "web", engine: "native" }];

const SYSTEM = {
  role: "system",
  content:
    "너는 공공도서관 수서 사서 보조다. 최신·시의성 정보(예: 현재 베스트셀러 순위)는 반드시 웹 검색으로 확인하고, " +
    "특정 도서의 소장 여부는 반드시 제공된 search_library_catalog 도구를 호출해 확인한다. 추측하지 말 것.",
};
const USER_BOTH = {
  role: "user",
  content:
    "2026년 현재 국내 종합 베스트셀러 소설 1위 도서가 무엇인지 웹에서 확인하고, " +
    "그 책이 우리 도서관에 소장되어 있는지 search_library_catalog 도구로 조회해줘.",
};

// ── 응답 분석 ─────────────────────────────────────────────────────
function analyze(r) {
  if (!r.ok || !r.json) {
    const errMsg = r.json?.error?.message || r.raw?.slice(0, 400) || r.error || "(no body)";
    return { fail: true, summary: `HTTP ${r.status} ✖ ${errMsg}` };
  }
  const choice = r.json.choices?.[0] || {};
  const msg = choice.message || {};
  const toolCalls = Array.isArray(msg.tool_calls) ? msg.tool_calls : [];
  const annotations = Array.isArray(msg.annotations) ? msg.annotations : [];
  const citations = annotations.filter(a => a?.type === "url_citation" || a?.url || a?.url_citation);
  const finish = choice.finish_reason;
  const contentSnippet = (typeof msg.content === "string" ? msg.content : "").replace(/\s+/g, " ").slice(0, 160);
  return {
    fail: false,
    toolCalls,
    toolCallNames: toolCalls.map(t => t.function?.name).filter(Boolean),
    citationCount: citations.length,
    annotationCount: annotations.length,
    finish,
    contentSnippet,
    usage: r.json.usage || null,
  };
}

function printResult(label, r) {
  console.log(`\n── ${label} ──`);
  console.log(`   status=${r.status} time=${r.ms}ms`);
  const a = analyze(r);
  if (a.fail) { console.log("   " + a.summary); return a; }
  console.log(`   finish_reason = ${a.finish}`);
  console.log(`   tool_calls    = ${a.toolCalls.length}${a.toolCallNames.length ? " [" + a.toolCallNames.join(", ") + "]" : ""}`);
  console.log(`   citations     = ${a.citationCount} (annotations total: ${a.annotationCount})`);
  if (a.usage) console.log(`   usage         = prompt ${a.usage.prompt_tokens ?? "?"} / completion ${a.usage.completion_tokens ?? "?"}`);
  if (a.contentSnippet) console.log(`   content       = "${a.contentSnippet}${a.contentSnippet.length >= 160 ? "…" : ""}"`);
  return a;
}

// ── 실행 ──────────────────────────────────────────────────────────
console.log("═".repeat(70));
console.log(` OpenRouter 그라운딩 + tools 동시 호출 스모크테스트`);
console.log(` model = ${MODEL}`);
console.log("═".repeat(70));

// 0) 모델 존재/tools 지원 확인
try {
  const mr = await fetch(`${BASE}/models`);
  const mj = await mr.json();
  const found = (mj.data || []).find(m => m.id === MODEL);
  if (!found) {
    console.log(`\n⚠ 경고: /models 목록에서 '${MODEL}' 를 찾지 못했습니다. ID를 확인하세요.`);
  } else {
    const sp = found.supported_parameters || [];
    console.log(`\n모델 확인: OK · tools 지원 = ${sp.includes("tools") ? "예" : "아니오(!)"}`);
    if (!sp.includes("tools")) console.log("  → tools 미지원 모델이면 chief ROUTE 위임에 부적합합니다.");
  }
} catch (e) {
  console.log(`\n⚠ /models 확인 실패(무시하고 진행): ${e.message}`);
}

// S1) 대조군: tools만
const s1 = await callOR({
  model: MODEL,
  messages: [SYSTEM, USER_BOTH],
  tools: [CATALOG_TOOL],
  tool_choice: "auto",
});
const a1 = printResult("S1 대조군 · tools 만 (그라운딩 X)", s1);

// S2) 대조군: 그라운딩만
const s2 = await callOR({
  model: MODEL,
  messages: [SYSTEM, { role: "user", content: "2026년 현재 국내 종합 베스트셀러 소설 1위가 무엇인지 웹에서 확인해서 알려줘." }],
  plugins: NATIVE_WEB,
});
const a2 = printResult("S2 대조군 · 그라운딩(native) 만 (tools X)", s2);

// S3) 핵심: 그라운딩 + tools 동시 (plugins 방식)
const s3 = await callOR({
  model: MODEL,
  messages: [SYSTEM, USER_BOTH],
  plugins: NATIVE_WEB,
  tools: [CATALOG_TOOL],
  tool_choice: "auto",
});
const a3 = printResult("S3 핵심 · 그라운딩 + tools 동시 (plugins:web/native)", s3);

// S3b) S3에서 tool_call이 나왔다면, 가짜 도구 결과를 넣고 2턴째에서 그라운딩 인용이 붙는지 확인
let a3b = null;
if (!a3.fail && a3.toolCalls.length > 0) {
  const tc = a3.toolCalls[0];
  const assistantMsg = s3.json.choices[0].message;
  const toolMsg = {
    role: "tool",
    tool_call_id: tc.id,
    content: JSON.stringify({ found: true, title: "(스텁) 조회된 도서", call_number: "813.7-ㄱ", available: true }),
  };
  const s3bResp = await callOR({
    model: MODEL,
    messages: [SYSTEM, USER_BOTH, assistantMsg, toolMsg],
    plugins: NATIVE_WEB,
    tools: [CATALOG_TOOL],
    tool_choice: "auto",
  });
  a3b = printResult("S3b · 도구결과 회신 후 2턴째 (그라운딩 인용 확인)", s3bResp);
}

// S4) 대안 경로: 모델 슬러그 :online 접미사 + tools
const s4 = await callOR({
  model: `${MODEL}:online`,
  messages: [SYSTEM, USER_BOTH],
  tools: [CATALOG_TOOL],
  tool_choice: "auto",
});
const a4 = printResult("S4 대안 · 모델:online 접미사 + tools", s4);

// ── 판정 ──────────────────────────────────────────────────────────
console.log("\n" + "═".repeat(70));
console.log(" 판정");
console.log("═".repeat(70));

const line = (k, v) => console.log(`  ${k.padEnd(42)} ${v}`);
line("S1 tools 단독 동작", a1.fail ? "✖ 실패" : (a1.toolCalls.length ? "✔ tool_call 발생" : "△ 200이나 tool_call 없음"));
line("S2 그라운딩 단독 동작", a2.fail ? "✖ 실패" : (a2.citationCount ? `✔ 인용 ${a2.citationCount}건` : "△ 200이나 인용 없음"));
line("S3 그라운딩+tools 동시 요청 수락", a3.fail ? "✖ 거부/오류" : "✔ 200 수락됨");
if (!a3.fail) {
  line("   └ 같은 요청에서 tool_call 발생", a3.toolCalls.length ? "✔ 예" : "— 아니오");
  line("   └ 같은 응답에 그라운딩 인용", a3.citationCount ? `✔ ${a3.citationCount}건` : "— (1턴엔 없을 수 있음)");
}
if (a3b) line("S3b 2턴째 그라운딩 인용", a3b.fail ? "✖ 실패" : (a3b.citationCount ? `✔ ${a3b.citationCount}건` : "△ 인용 없음"));
line("S4 :online + tools 수락", a4.fail ? "✖ 거부/오류" : "✔ 200 수락됨");

console.log("\n결론:");
if (a3.fail && a4.fail) {
  console.log("  ✖ 그라운딩과 tools를 한 요청에 함께 쓰는 것이 거부되었습니다(양 경로 모두).");
  console.log("    → B-01은 그라운딩과 tools를 분리(2단계 호출)하거나 다른 소스를 검토해야 합니다.");
} else {
  const okPath = !a3.fail ? "plugins:web/native" : "model:online";
  const groundedSeen = (!a3.fail && a3.citationCount) || (a3b && a3b.citationCount) || (!a4.fail && a4.citationCount);
  console.log(`  ✔ 그라운딩 + tools 동시 요청이 수락됩니다 (경로: ${okPath}).`);
  console.log(`    실제 웹 인용 관측: ${groundedSeen ? "예" : "이번 실행에선 미관측(모델이 검색 불필요로 판단했을 수 있음 — 프롬프트/재시도 확인)"}.`);
  console.log("    → CHAT_MODELS에 그라운딩 Gemini 추가 가능. 단 도메인 필터 미지원·쿼리당 과금 유의.");
}
console.log("");
