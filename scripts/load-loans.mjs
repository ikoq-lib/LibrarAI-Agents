/**
 * 대출내역 적재기
 *
 * 도서관 시스템에서 추출한 대출내역 엑셀(.xlsx) 또는 CSV를 public.loans 에 적재한다.
 * db/acquisition_scoring.sql 이 먼저 적용돼 있어야 한다.
 *
 * 개인정보 처리:
 * - 이용자성명은 읽지도, 저장하지도 않는다(헤더만 확인하고 값은 버린다).
 * - 대출회원번호는 sha256(salt + 번호) 해시로만 저장한다. 원본은 DB에 남지 않는다.
 * - 같은 salt 를 계속 써야 회차별 적재분이 동일 회원으로 이어진다. 반드시 고정 보관할 것.
 *
 * 사용법:
 *   node scripts/load-loans.mjs "References/240101~260731대출내역(전체).xlsx"
 *   node scripts/load-loans.mjs <file> --dry-run          DB 접속 없이 품질 점검만
 *   node scripts/load-loans.mjs <file> --replace           loans 를 비우고 전체 재적재
 *   node scripts/load-loans.mjs <file> --sheet 대출내역    시트 지정
 *   node scripts/load-loans.mjs <file> --no-refresh        통계 MV 갱신 생략
 *
 * 환경변수:
 * - LOANS_MEMBER_SALT   (필수) 회원번호 해시 솔트
 * - SUPABASE_DB_PASSWORD (--dry-run 이 아니면 필수)
 *
 * 재실행 안전성:
 *   loans_dedup_uidx (member_hash, reg_no, loan_date, title_raw) nulls not distinct 에 기대어
 *   on conflict do nothing 으로 넣는다. 회원번호나 등록번호가 비어도 중복 판정 대상이라
 *   같은 파일을 몇 번 돌려도 행이 늘지 않는다.
 */
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import crypto from "node:crypto";
import pg from "pg";
import { pathToFileURL } from "node:url";

const { Pool } = pg;

const DB_HOST = "aws-0-ap-southeast-1.pooler.supabase.com";
const DB_USER = "postgres.tkyaganfdfiuesvbcbkr";
const DEFAULT_SHEET = "대출내역";
const DEFAULT_BATCH = Number(process.env.LOANS_BATCH_SIZE || 2000);
// 연속 결손일이 이 값 이상이면 추출 누락으로 보고 경고한다.
// 2024-01-01~2026-07-31 원본에서 2025-12-14~31(18일) 구멍이 이 규칙으로 잡힌다.
const GAP_ALERT_DAYS = Number(process.env.LOANS_GAP_ALERT_DAYS || 5);

// ---------------------------------------------------------------------------
// 최소 XLSX 리더 - 외부 의존성 없이 ZIP(deflate/stored) + SpreadsheetML 만 다룬다.
// ---------------------------------------------------------------------------

/** ZIP 중앙 디렉터리를 훑어 { 파일명: Buffer } 로 푼다. */
export function unzip(buf) {
  // EOCD(End Of Central Directory) 시그니처를 뒤에서부터 찾는다.
  let eocd = -1;
  for (let i = buf.length - 22; i >= 0 && i >= buf.length - 66_000; i--) {
    if (buf.readUInt32LE(i) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error("ZIP 구조를 찾을 수 없습니다(손상된 xlsx?)");

  const count = buf.readUInt16LE(eocd + 10);
  let ptr = buf.readUInt32LE(eocd + 16);
  const out = new Map();

  for (let n = 0; n < count; n++) {
    if (buf.readUInt32LE(ptr) !== 0x02014b50) break;
    const method = buf.readUInt16LE(ptr + 10);
    const compSize = buf.readUInt32LE(ptr + 20);
    const nameLen = buf.readUInt16LE(ptr + 28);
    const extraLen = buf.readUInt16LE(ptr + 30);
    const commentLen = buf.readUInt16LE(ptr + 32);
    const localOff = buf.readUInt32LE(ptr + 42);
    const name = buf.toString("utf8", ptr + 46, ptr + 46 + nameLen);

    // 로컬 헤더는 중앙 디렉터리와 extra 길이가 다를 수 있어 다시 읽는다.
    const lNameLen = buf.readUInt16LE(localOff + 26);
    const lExtraLen = buf.readUInt16LE(localOff + 28);
    const dataStart = localOff + 30 + lNameLen + lExtraLen;
    const raw = buf.subarray(dataStart, dataStart + compSize);

    if (method === 0) out.set(name, Buffer.from(raw));
    else if (method === 8) out.set(name, zlib.inflateRawSync(raw));
    // 그 외 압축 방식(bzip2 등)은 엑셀이 쓰지 않으므로 건너뛴다.

    ptr += 46 + nameLen + extraLen + commentLen;
  }
  return out;
}

const XML_ENTITY = { amp: "&", lt: "<", gt: ">", quot: '"', apos: "'" };
function unescapeXml(s) {
  return s.replace(/&(amp|lt|gt|quot|apos|#x?[0-9a-fA-F]+);/g, (m, e) => {
    if (XML_ENTITY[e]) return XML_ENTITY[e];
    if (e[0] === "#") {
      const code = e[1] === "x" || e[1] === "X"
        ? parseInt(e.slice(2), 16)
        : parseInt(e.slice(1), 10);
      return Number.isFinite(code) ? String.fromCodePoint(code) : m;
    }
    return m;
  });
}

/** sharedStrings.xml -> 문자열 배열. <si> 안의 모든 <t> 를 이어붙인다(리치텍스트 대응). */
export function parseSharedStrings(xml) {
  if (!xml) return [];
  const out = [];
  for (const si of xml.match(/<si\b[^>]*\/>|<si\b[^>]*>[\s\S]*?<\/si>/g) || []) {
    let s = "";
    for (const t of si.match(/<t\b[^>]*>[\s\S]*?<\/t>/g) || []) {
      s += unescapeXml(t.replace(/^<t\b[^>]*>/, "").replace(/<\/t>$/, ""));
    }
    out.push(s);
  }
  return out;
}

/** 엑셀 열 이름(A, B, ..., AA) -> 0-based 인덱스 */
export function colIndex(ref) {
  let n = 0;
  for (const ch of ref.replace(/[^A-Z]/g, "")) n = n * 26 + (ch.charCodeAt(0) - 64);
  return n - 1;
}

/** 엑셀 날짜 일련번호 -> 'YYYY-MM-DD'. 1900 윤년 버그를 감안한 표준 기준일 사용. */
export function serialToDate(serial) {
  const ms = Date.UTC(1899, 11, 30) + Math.round(serial) * 86_400_000;
  return new Date(ms).toISOString().slice(0, 10);
}

/** 워크시트 XML -> 행 배열(각 행은 셀 문자열 배열). 값은 모두 문자열로 돌려준다. */
export function parseSheet(xml, shared) {
  const rows = [];
  for (const rowXml of xml.match(/<row\b[^>]*\/>|<row\b[^>]*>[\s\S]*?<\/row>/g) || []) {
    const cells = [];
    for (const cellXml of rowXml.match(/<c\b[^>]*\/>|<c\b[^>]*>[\s\S]*?<\/c>/g) || []) {
      const refMatch = cellXml.match(/\br="([A-Z]+)\d+"/);
      const idx = refMatch ? colIndex(refMatch[1]) : cells.length;
      const type = (cellXml.match(/\bt="([^"]+)"/) || [])[1] || "n";

      let value = "";
      if (type === "inlineStr") {
        for (const t of cellXml.match(/<t\b[^>]*>[\s\S]*?<\/t>/g) || []) {
          value += unescapeXml(t.replace(/^<t\b[^>]*>/, "").replace(/<\/t>$/, ""));
        }
      } else {
        const v = cellXml.match(/<v\b[^>]*>([\s\S]*?)<\/v>/);
        if (v) {
          const rawValue = unescapeXml(v[1]);
          value = type === "s" ? (shared[Number(rawValue)] ?? "") : rawValue;
        }
      }
      while (cells.length < idx) cells.push("");
      cells[idx] = value;
    }
    rows.push(cells);
  }
  return rows;
}

/** xlsx 파일 -> 행 배열. sheetName 이 없으면 첫 시트를 쓴다. */
export function readXlsx(file, sheetName) {
  const zip = unzip(fs.readFileSync(file));
  const wbXml = zip.get("xl/workbook.xml")?.toString("utf8") || "";
  const relXml = zip.get("xl/_rels/workbook.xml.rels")?.toString("utf8") || "";

  const sheets = [...wbXml.matchAll(/<sheet\b[^>]*\/>/g)].map((m) => ({
    name: unescapeXml((m[0].match(/name="([^"]*)"/) || [])[1] || ""),
    rid: (m[0].match(/r:id="([^"]*)"/) || [])[1] || "",
  }));
  if (!sheets.length) throw new Error("워크시트를 찾을 수 없습니다");

  const picked = sheetName ? sheets.find((s) => s.name === sheetName) : sheets[0];
  if (!picked) {
    throw new Error(`시트 '${sheetName}' 없음. 사용 가능: ${sheets.map((s) => s.name).join(", ")}`);
  }

  const rels = Object.fromEntries(
    [...relXml.matchAll(/<Relationship\b[^>]*\/>/g)].map((m) => [
      (m[0].match(/Id="([^"]*)"/) || [])[1],
      (m[0].match(/Target="([^"]*)"/) || [])[1],
    ]),
  );
  let target = rels[picked.rid] || "worksheets/sheet1.xml";
  target = target.replace(/^\/?xl\//, "").replace(/^\//, "");

  const sheetXml = (zip.get(`xl/${target}`) || zip.get("xl/worksheets/sheet1.xml"))?.toString("utf8");
  if (!sheetXml) throw new Error(`시트 데이터를 찾을 수 없습니다: xl/${target}`);

  return {
    sheetName: picked.name,
    rows: parseSheet(sheetXml, parseSharedStrings(zip.get("xl/sharedStrings.xml")?.toString("utf8"))),
  };
}

/** CSV -> 행 배열 (따옴표 이스케이프 지원). */
export function parseCsv(text) {
  const rows = [];
  let row = [];
  let cur = "";
  let quoted = false;
  const DQ = '"';
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === DQ) {
        if (text[i + 1] === DQ) { cur += DQ; i++; } else quoted = false;
      } else cur += ch;
    } else if (ch === DQ) quoted = true;
    else if (ch === ",") { row.push(cur); cur = ""; }
    else if (ch === "\n") { row.push(cur); rows.push(row); row = []; cur = ""; }
    else if (ch !== "\r") cur += ch;
  }
  if (cur || row.length) { row.push(cur); rows.push(row); }
  return rows;
}

// ---------------------------------------------------------------------------
// 필드 정규화
// ---------------------------------------------------------------------------

/** 헤더 후보. 도서관 시스템마다 표기가 달라 여러 이름을 받는다. */
const HEADER_ALIASES = {
  member: ["대출회원번호", "회원번호", "이용자번호", "회원ID"],
  name: ["이용자성명", "성명", "이름", "이용자명"],          // 읽고 버린다
  patronType: ["신분", "이용자구분", "회원구분"],
  regNo: ["등록번호", "자료등록번호", "바코드"],
  title: ["서명", "도서명", "자료명", "제목"],
  loanDate: ["대출일", "대출일자", "대출날짜"],
  room: ["자료실", "소장자료실", "resource_room"],
  callNo: ["청구기호", "청구기호명"],
  sourceLibrary: ["도서관", "소장도서관", "신청도서관", "관명"],
};

/** 헤더 행에서 컬럼 인덱스를 찾는다. 순서가 바뀌어도 동작한다. */
export function mapHeader(headerRow) {
  const norm = headerRow.map((h) => String(h ?? "").replace(/\s+/g, "").trim());
  const map = {};
  for (const [key, aliases] of Object.entries(HEADER_ALIASES)) {
    const idx = norm.findIndex((h) => h && aliases.some((a) => h === a.replace(/\s+/g, "")));
    if (idx >= 0) map[key] = idx;
  }
  return map;
}

/**
 * 헤더 폭을 넘어가는 무명 컬럼을 찾는다.
 * 2024~2026 원본에는 2025-09~12 구간에만 값이 있는 이름 없는 10번째 열(도서관명)이 있다.
 * 의미가 확정되지 않았으므로 버리지 않고 source_library 에 원문 그대로 담는다.
 */
export function findUnnamedColumn(rows, headerWidth) {
  const counts = new Map();
  for (const row of rows) {
    for (let i = headerWidth; i < row.length; i++) {
      if (String(row[i] ?? "").trim()) counts.set(i, (counts.get(i) || 0) + 1);
    }
  }
  if (!counts.size) return null;
  const [index, count] = [...counts.entries()].sort((a, b) => b[1] - a[1])[0];
  const samples = [];
  for (const row of rows) {
    const v = String(row[index] ?? "").trim();
    if (v && !samples.includes(v)) samples.push(v);
    if (samples.length >= 3) break;
  }
  return { index, count, samples };
}

/** 회원 신분 문자열 -> age_group. */
export function ageGroupOf(patronType) {
  const s = String(patronType ?? "");
  if (!s) return "other";
  if (s.includes("어린이") || s.includes("유아")) return "child";
  if (s.includes("학생") || s.includes("청소년")) return "youth";
  if (s.includes("순회문고") || s.includes("단체") || s.includes("기관")) return "other";
  return "adult";
}

/** 여러 형식으로 들어오는 대출일을 'YYYY-MM-DD' 로 통일한다. */
export function normalizeDate(value) {
  if (value == null) return null;
  if (value instanceof Date) return value.toISOString().slice(0, 10);

  const s = String(value).trim();
  if (!s) return null;

  // 20240106 (8자리). 엑셀 일련번호는 5자리를 넘지 않으므로 먼저 판별해도 충돌이 없다.
  let m = s.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (m && Number(m[2]) >= 1 && Number(m[2]) <= 12 && Number(m[3]) >= 1 && Number(m[3]) <= 31) {
    return `${m[1]}-${m[2]}-${m[3]}`;
  }
  // 엑셀 일련번호(1990~2090년 범위만 날짜로 취급)
  if (/^\d+(\.\d+)?$/.test(s)) {
    const n = Number(s);
    if (n >= 32_874 && n <= 69_400) return serialToDate(n);
    return null;
  }
  // 2024-01-01 / 2024-01-01 00:00:00 / 2024-01-01T00:00:00Z
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m) return `${m[1]}-${m[2]}-${m[3]}`;
  // 2024.1.6 / 2024/01/06
  m = s.match(/^(\d{4})[./](\d{1,2})[./](\d{1,2})/);
  if (m) return `${m[1]}-${String(m[2]).padStart(2, "0")}-${String(m[3]).padStart(2, "0")}`;
  return null;
}

export function hashMember(memberNo, salt) {
  const s = String(memberNo ?? "").trim();
  if (!s) return null;
  return crypto.createHash("sha256").update(`${salt}:${s}`).digest("hex");
}

/**
 * 원본 행 -> loans 행. 이용자성명은 어떤 경로로도 결과에 담기지 않는다.
 * 반환 null 은 적재 불가(대출일 파싱 실패 등)를 뜻한다.
 */
export function toLoanRow(row, map, salt) {
  const at = (key) => (map[key] == null ? null : row[map[key]] ?? null);
  const str = (v) => {
    const s = String(v ?? "").trim();
    return s === "" ? null : s;
  };

  const loanDate = normalizeDate(at("loanDate"));
  if (!loanDate) return null;

  const patronType = str(at("patronType"));
  return {
    member_hash: hashMember(at("member"), salt),
    patron_type: patronType,
    age_group: ageGroupOf(patronType),
    reg_no: str(at("regNo")),
    title_raw: str(at("title")),
    loan_date: loanDate,
    room: str(at("room")),
    call_no: str(at("callNo")),
    source_library: str(at("sourceLibrary")),
  };
}

/** 대출이 하루도 없는 연속 구간 중 minDays 이상인 것을 찾는다(추출 누락 탐지). */
export function findDateGaps(dates, minDays = GAP_ALERT_DAYS) {
  const present = new Set(dates);
  const sorted = [...present].sort();
  if (sorted.length < 2) return [];

  const gaps = [];
  const dayMs = 86_400_000;
  for (let i = 0; i < sorted.length - 1; i++) {
    const a = Date.parse(`${sorted[i]}T00:00:00Z`);
    const b = Date.parse(`${sorted[i + 1]}T00:00:00Z`);
    const missing = Math.round((b - a) / dayMs) - 1;
    if (missing >= minDays) {
      gaps.push({
        from: new Date(a + dayMs).toISOString().slice(0, 10),
        to: new Date(b - dayMs).toISOString().slice(0, 10),
        days: missing,
      });
    }
  }
  return gaps;
}

// ---------------------------------------------------------------------------
// 적재
// ---------------------------------------------------------------------------

const COLUMNS = [
  "member_hash", "patron_type", "age_group", "reg_no",
  "title_raw", "loan_date", "room", "call_no", "source_library",
];

function chunk(list, size) {
  const out = [];
  for (let i = 0; i < list.length; i += size) out.push(list.slice(i, i + size));
  return out;
}

async function insertBatch(client, batch) {
  const values = batch
    .map((_, r) => `(${COLUMNS.map((_, c) => `$${r * COLUMNS.length + c + 1}`).join(",")})`)
    .join(",");
  const params = batch.flatMap((row) => COLUMNS.map((c) => row[c]));
  const res = await client.query(
    `insert into public.loans (${COLUMNS.join(",")}) values ${values} on conflict do nothing`,
    params,
  );
  return res.rowCount;
}

function required(name) {
  const v = process.env[name];
  if (!v) throw new Error(`환경변수 ${name} 가 필요합니다`);
  return v;
}

function parseArgs(argv) {
  const opts = { file: null, sheet: null, dryRun: false, replace: false, refresh: true };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dry-run") opts.dryRun = true;
    else if (a === "--replace") opts.replace = true;
    else if (a === "--no-refresh") opts.refresh = false;
    else if (a === "--sheet") opts.sheet = argv[++i];
    else if (!a.startsWith("--") && !opts.file) opts.file = a;
  }
  return opts;
}

export async function run(argv = process.argv.slice(2)) {
  const opts = parseArgs(argv);
  if (!opts.file) {
    console.error("사용법: node scripts/load-loans.mjs <대출내역.xlsx|csv> [--dry-run] [--replace] [--sheet 이름]");
    process.exitCode = 1;
    return;
  }
  if (!fs.existsSync(opts.file)) throw new Error(`파일을 찾을 수 없습니다: ${opts.file}`);

  const salt = required("LOANS_MEMBER_SALT");

  // --- 읽기 ---------------------------------------------------------------
  const ext = path.extname(opts.file).toLowerCase();
  let rows;
  let sheetName = "(csv)";
  if (ext === ".csv") {
    rows = parseCsv(fs.readFileSync(opts.file, "utf8"));
  } else {
    const parsed = readXlsx(opts.file, opts.sheet || undefined);
    // 시트명을 지정하지 않았고 기본 시트가 따로 있으면 그쪽을 우선한다.
    if (!opts.sheet && parsed.sheetName !== DEFAULT_SHEET) {
      try {
        const preferred = readXlsx(opts.file, DEFAULT_SHEET);
        rows = preferred.rows;
        sheetName = preferred.sheetName;
      } catch {
        rows = parsed.rows;
        sheetName = parsed.sheetName;
      }
    } else {
      rows = parsed.rows;
      sheetName = parsed.sheetName;
    }
  }
  if (!rows.length) throw new Error("빈 파일입니다");

  const map = mapHeader(rows[0]);
  const missing = ["member", "regNo", "loanDate"].filter((k) => map[k] == null);
  if (missing.length) {
    throw new Error(
      `필수 컬럼을 찾지 못했습니다: ${missing.join(", ")}\n` +
      `헤더: ${rows[0].join(" | ")}`,
    );
  }

  console.log(`파일   : ${opts.file}`);
  console.log(`시트   : ${sheetName}`);
  console.log(`헤더   : ${rows[0].filter(Boolean).join(" | ")}`);
  if (map.name != null) {
    console.log("주의   : 이용자성명 컬럼을 발견했습니다. 값은 읽지 않고 버립니다(DB 미저장).");
  }
  if (map.sourceLibrary == null) {
    const unnamed = findUnnamedColumn(rows.slice(1), rows[0].length);
    if (unnamed) {
      map.sourceLibrary = unnamed.index;
      console.log(
        `참고   : 헤더 없는 ${unnamed.index + 1}번째 열에 값 ${unnamed.count}건을 발견했습니다 ` +
        `(예: ${unnamed.samples.join(", ")}). source_library 에 원문 그대로 담습니다.`,
      );
    } else {
      console.log("참고   : 도서관명 컬럼이 없습니다. source_library 는 비워둡니다.");
    }
  }

  // --- 변환 ---------------------------------------------------------------
  const loans = [];
  const seen = new Set();
  let skippedDate = 0;
  let dupInFile = 0;
  let noMember = 0;
  let noRegNo = 0;

  for (const row of rows.slice(1)) {
    if (!row.some((v) => String(v ?? "").trim())) continue;
    const loan = toLoanRow(row, map, salt);
    if (!loan) { skippedDate++; continue; }
    if (!loan.member_hash) noMember++;
    if (!loan.reg_no) noRegNo++;

    // 파일 안의 완전 중복은 DB 왕복 전에 걸러낸다.
    // 키는 loans_dedup_uidx 와 동일해야 한다 - 값이 비어도 제외하지 않는다.
    const key = [loan.member_hash, loan.reg_no, loan.loan_date, loan.title_raw].join("\u0000");
    if (seen.has(key)) { dupInFile++; continue; }
    seen.add(key);
    loans.push(loan);
  }

  const dates = loans.map((l) => l.loan_date);
  const minDate = dates.reduce((a, b) => (a < b ? a : b));
  const maxDate = dates.reduce((a, b) => (a > b ? a : b));
  const gaps = findDateGaps(dates);

  console.log("");
  console.log(`원본 행 : ${rows.length - 1}`);
  console.log(`적재 대상: ${loans.length}`);
  console.log(`  대출일 파싱 실패로 제외 : ${skippedDate}`);
  console.log(`  파일 내 중복으로 제외   : ${dupInFile}`);
  console.log(`  회원번호 없음(해시 null): ${noMember}`);
  console.log(`  등록번호 없음           : ${noRegNo}`);
  console.log(`기간   : ${minDate} ~ ${maxDate}`);

  const nullKeyRows = loans.filter((l) => !l.member_hash || !l.reg_no).length;
  if (nullKeyRows) {
    console.log(`참고   : 회원번호 또는 등록번호가 빈 ${nullKeyRows}행이 있습니다(서명으로 중복 판정).`);
  }

  if (gaps.length) {
    console.log("");
    console.log(`경고: 대출이 ${GAP_ALERT_DAYS}일 이상 연속으로 없는 구간 ${gaps.length}건 - 추출 누락일 수 있습니다.`);
    for (const g of gaps) console.log(`  ${g.from} ~ ${g.to} (${g.days}일)`);
  }

  if (opts.dryRun) {
    console.log("\n--dry-run 이므로 DB에 쓰지 않고 종료합니다.");
    return { inserted: 0, prepared: loans.length, gaps, dryRun: true };
  }

  // --- 적재 ---------------------------------------------------------------
  const pool = new Pool({
    host: DB_HOST,
    port: 5432,
    user: DB_USER,
    password: required("SUPABASE_DB_PASSWORD"),
    database: "postgres",
    ssl: { rejectUnauthorized: false },
    max: 2,
  });
  const client = await pool.connect();
  let inserted = 0;

  try {
    const exists = await client.query("select to_regclass('public.loans') as t");
    if (!exists.rows[0].t) {
      throw new Error("public.loans 가 없습니다. db/acquisition_scoring.sql 을 먼저 적용하세요.");
    }

    await client.query("begin");
    if (opts.replace) {
      const before = await client.query("select count(*)::int n from public.loans");
      await client.query("truncate table public.loans");
      console.log(`\n--replace: 기존 ${before.rows[0].n}행을 비웠습니다.`);
    }

    console.log("");
    const batches = chunk(loans, DEFAULT_BATCH);
    for (let i = 0; i < batches.length; i++) {
      inserted += await insertBatch(client, batches[i]);
      if ((i + 1) % 10 === 0 || i === batches.length - 1) {
        console.log(`  적재 ${i + 1}/${batches.length} 배치 (누적 ${inserted}행)`);
      }
    }

    // 노출기간 정규화의 기준이 되는 대출 데이터 구간을 갱신한다.
    await client.query(
      `insert into public.loan_window (id, start_date, end_date, note)
       values (true, $1, $2, $3)
       on conflict (id) do update
         set start_date = least(public.loan_window.start_date, excluded.start_date),
             end_date   = greatest(public.loan_window.end_date, excluded.end_date),
             note       = excluded.note`,
      [minDate, maxDate, `${path.basename(opts.file)} 적재 (${new Date().toISOString().slice(0, 10)})`
        + (gaps.length ? ` / 결손 ${gaps.map((g) => `${g.from}~${g.to}`).join(", ")}` : "")],
    );

    await client.query("commit");
    console.log(`\n적재 완료: 신규 ${inserted}행 / 기존 중복 ${loans.length - inserted}행 무시`);

    // --- 검증 -------------------------------------------------------------
    const total = await client.query("select count(*)::int n from public.loans");
    const joined = await client.query(
      `select count(distinct l.reg_no)::int matched,
              (select count(distinct reg_no)::int from public.loans where reg_no is not null) total
         from public.loans l join public.books b on b.reg_no = l.reg_no`,
    );
    const j = joined.rows[0];
    console.log(`loans 총 행수 : ${total.rows[0].n}`);
    console.log(`books 조인율  : ${j.matched}/${j.total} (${(j.matched / j.total * 100).toFixed(1)}%)`);
    if (j.matched / j.total < 0.7) {
      console.log("  경고: 조인율이 70% 미만입니다. 등록번호 체계가 장서 목록과 다를 수 있습니다.");
    }

    if (opts.refresh) {
      console.log("\n통계 MV 갱신 중...");
      const t0 = Date.now();
      // concurrently 는 함수/트랜잭션 안에서 실행할 수 없어 여기서 직접 돌린다.
      // mv_book_usage 가 나머지 셋의 원본이므로 순서를 지킨다.
      const MVS = ["mv_book_usage", "mv_publisher_stats", "mv_author_stats", "mv_kdc_deficit"];
      for (const mv of MVS) {
        try {
          await client.query(`refresh materialized view concurrently public.${mv}`);
        } catch (err) {
          // 유니크 인덱스가 없거나 아직 한 번도 채워지지 않은 MV 는 비동시 갱신으로 되돌린다.
          console.log(`  ${mv}: concurrently 실패(${err.message}) → 일반 refresh 로 재시도`);
          await client.query(`refresh materialized view public.${mv}`);
        }
      }
      console.log(`  완료 (${((Date.now() - t0) / 1000).toFixed(1)}초)`);
      const stats = await client.query(
        `select (select count(*)::int from public.mv_publisher_stats) pubs,
                (select count(*)::int from public.mv_author_stats) auts`,
      );
      console.log(`  출판사 ${stats.rows[0].pubs}곳 / 저자 ${stats.rows[0].auts}명 통계 갱신됨`);
    } else {
      console.log("\n--no-refresh: 통계 MV 를 갱신하지 않았습니다.");
      console.log("  점수에 반영하려면 select public.refresh_acquisition_stats(); 를 실행하세요.");
    }
  } catch (err) {
    await client.query("rollback").catch(() => {});
    throw err;
  } finally {
    client.release();
    await pool.end();
  }

  return { inserted, prepared: loans.length, gaps, dryRun: false };
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  run().catch((err) => {
    console.error(`\n실패: ${err.message}`);
    process.exitCode = 1;
  });
}
