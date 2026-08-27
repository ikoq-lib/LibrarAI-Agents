/**
 * 자료 등록일(입수시기) 적재기
 *
 * 도서관은 등록번호를 입수 순서대로 매기므로, [시작등록번호, 끝등록번호] 구간이
 * 곧 "그 기간에 입수된 도서"를 뜻한다. 실제 등록일은 확보할 수 없어 반월(상/하반기)
 * 단위 구간표만 있으며, 이 스크립트는 구간을 public.book_registration_periods 에 적재하고
 * public.books.acquired_date 를 채운다.
 *
 * 추정 방식:
 * - 상반기(1~15일) -> 그 달 8일,  하반기(16~말일) -> 그 달 23일 (구간 중앙값)
 *   중앙값을 쓰면 기대 오차가 최소가 된다(최대 ±8일).
 * - 구간표보다 앞선 등록번호는 2018년 도서관리시스템 교체 이전이라 자료가 없다.
 *   PRE_2019_DATE 단일 대체값을 넣고 acquired_date_precision='pre_2019' 로 표시한다.
 *
 * 이 대체값이 지금 계산에 미치는 영향:
 *   회전율의 노출기간은 max(대출데이터 시작일, acquired_date) 부터 센다.
 *   대출 데이터가 2024-01-01 부터라 2024년 이전 값은 무엇을 넣든 결과가 같다.
 *   즉 대체값 선택은 현재 점수에 영향이 없고, 대출 이력이 2019년 이전까지 확장될 때만 의미가 생긴다.
 *
 * 사용법:
 *   node scripts/load-acquisition-dates.mjs "References/도서 등록일.xlsx"
 *   node scripts/load-acquisition-dates.mjs <file> --dry-run     검증만
 *   node scripts/load-acquisition-dates.mjs <file> --no-refresh  통계 MV 갱신 생략
 *
 * 환경변수:
 * - SUPABASE_DB_PASSWORD (--dry-run 이 아니면 필수)
 */
import fs from "node:fs";
import pg from "pg";
import { pathToFileURL } from "node:url";

import { readXlsx, parseCsv } from "./load-loans.mjs";

const { Pool } = pg;

const DB_HOST = "aws-0-ap-southeast-1.pooler.supabase.com";
const DB_USER = "postgres.tkyaganfdfiuesvbcbkr";

// 구간표 이전(2019-01 이전) 등록번호에 넣을 단일 대체값.
// 2018년 도서관리시스템 교체 시점 직전으로 잡았다. 실제 입수 시기 정보가 아니다.
export const PRE_2019_DATE = "2018-12-31";

// 반월 구간의 중앙값. 상반기 1~15일 -> 8일, 하반기 16~말일 -> 23일.
export const HALF_MID_DAY = { 상: 8, 하: 23 };

// ---------------------------------------------------------------------------
// 파싱 / 검증
// ---------------------------------------------------------------------------

/** 'EM181905' / 'EM0181905' / '181905' -> 181905. 판별 불가면 null. */
export function regNoToNum(v) {
  const s = String(v ?? "").trim().toUpperCase();
  const m = s.match(/^(?:EM)?0*(\d+)$/);
  return m ? Number(m[1]) : null;
}

/** 연/월/반기 -> 추정일(구간 중앙값). */
export function estimateDate(year, month, half) {
  const day = HALF_MID_DAY[half];
  if (!day) return null;
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

const HEADER_ALIASES = {
  year: ["연도", "년도", "년"],
  month: ["월"],
  half: ["기간", "반기", "상하"],
  startNo: ["시작등록번호EM", "시작등록번호", "시작번호"],
  endNo: ["끝등록번호EM", "끝등록번호", "끝번호", "종료등록번호"],
};

export function mapHeader(headerRow) {
  const norm = headerRow.map((h) => String(h ?? "").replace(/\s+/g, ""));
  const map = {};
  for (const [key, aliases] of Object.entries(HEADER_ALIASES)) {
    const idx = norm.findIndex((h) => h && aliases.some((a) => h === a.replace(/\s+/g, "")));
    if (idx >= 0) map[key] = idx;
  }
  return map;
}

/** 행 배열 -> 구간 목록. 형식이 깨진 행은 skipped 로 돌려준다. */
export function parseRanges(rows) {
  const map = mapHeader(rows[0]);
  const missing = ["year", "month", "half", "startNo", "endNo"].filter((k) => map[k] == null);
  if (missing.length) {
    throw new Error(`필수 컬럼을 찾지 못했습니다: ${missing.join(", ")}\n헤더: ${rows[0].join(" | ")}`);
  }

  const periods = [];
  const skipped = [];
  for (const row of rows.slice(1)) {
    if (!row.some((v) => String(v ?? "").trim())) continue;
    const year = Number(String(row[map.year] ?? "").trim());
    const month = Number(String(row[map.month] ?? "").trim());
    const half = String(row[map.half] ?? "").trim();
    const startNum = regNoToNum(row[map.startNo]);
    const endNum = regNoToNum(row[map.endNo]);

    if (!Number.isInteger(year) || !Number.isInteger(month) || month < 1 || month > 12
        || !HALF_MID_DAY[half] || startNum == null || endNum == null) {
      skipped.push(row);
      continue;
    }
    periods.push({ year, month, half, startNum, endNum, estDate: estimateDate(year, month, half) });
  }
  return { periods, skipped };
}

/**
 * 구간표 정합성 검사.
 * 등록번호는 입수 순서대로 매겨지므로 (a) 구간이 겹치면 안 되고,
 * (b) 시간순으로 정렬했을 때 번호가 단조 증가해야 한다.
 * 번호 공백(gap)은 폐기·결번으로 생길 수 있어 오류가 아니라 정보로만 보고한다.
 */
export function validateRanges(periods) {
  const issues = [];
  const inverted = periods.filter((p) => p.endNum < p.startNum);
  for (const p of inverted) {
    issues.push({ kind: "inverted", detail: `${p.year}-${p.month} ${p.half}: 끝(${p.endNum}) < 시작(${p.startNum})` });
  }

  const dupKey = new Set();
  for (const p of periods) {
    const k = `${p.year}-${p.month}-${p.half}`;
    if (dupKey.has(k)) issues.push({ kind: "duplicate", detail: `${k} 구간이 중복 정의됨` });
    dupKey.add(k);
  }

  const byNum = [...periods].sort((a, b) => a.startNum - b.startNum);
  const gaps = [];
  for (let i = 1; i < byNum.length; i++) {
    const prev = byNum[i - 1];
    const cur = byNum[i];
    if (cur.startNum <= prev.endNum) {
      issues.push({
        kind: "overlap",
        detail: `${prev.year}-${prev.month}${prev.half}(~${prev.endNum}) 과 ${cur.year}-${cur.month}${cur.half}(${cur.startNum}~) 이 겹침`,
      });
    } else if (cur.startNum > prev.endNum + 1) {
      gaps.push({ from: prev.endNum + 1, to: cur.startNum - 1, count: cur.startNum - prev.endNum - 1 });
    }
  }

  const half = (p) => (p.half === "상" ? 0 : 1);
  const chrono = [...periods].sort((a, b) => a.year - b.year || a.month - b.month || half(a) - half(b));
  for (let i = 1; i < chrono.length; i++) {
    if (chrono[i].startNum < chrono[i - 1].startNum) {
      issues.push({
        kind: "non_monotonic",
        detail: `${chrono[i - 1].year}-${chrono[i - 1].month}${chrono[i - 1].half} 다음인 `
          + `${chrono[i].year}-${chrono[i].month}${chrono[i].half} 의 시작번호가 더 작음`,
      });
    }
  }

  return {
    issues,
    gaps,
    minNum: byNum.length ? byNum[0].startNum : null,
    maxNum: byNum.length ? byNum[byNum.length - 1].endNum : null,
  };
}

/** 커버되지 않는 달을 찾는다(등록이 없던 달일 수도 있으므로 경고가 아니라 정보). */
export function missingMonths(periods) {
  if (!periods.length) return [];
  const have = new Set(periods.map((p) => `${p.year}-${String(p.month).padStart(2, "0")}`));
  const sorted = [...periods].sort((a, b) => a.year - b.year || a.month - b.month);
  const first = sorted[0];
  const last = sorted[sorted.length - 1];
  const out = [];
  for (let y = first.year; y <= last.year; y++) {
    for (let m = 1; m <= 12; m++) {
      if (y === first.year && m < first.month) continue;
      if (y === last.year && m > last.month) continue;
      const k = `${y}-${String(m).padStart(2, "0")}`;
      if (!have.has(k)) out.push(k);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// 적재
// ---------------------------------------------------------------------------

function required(name) {
  const v = process.env[name];
  if (!v) throw new Error(`환경변수 ${name} 가 필요합니다`);
  return v;
}

function parseArgs(argv) {
  const opts = { file: null, dryRun: false, refresh: true };
  for (const a of argv) {
    if (a === "--dry-run") opts.dryRun = true;
    else if (a === "--no-refresh") opts.refresh = false;
    else if (!a.startsWith("--") && !opts.file) opts.file = a;
  }
  return opts;
}

export async function run(argv = process.argv.slice(2)) {
  const opts = parseArgs(argv);
  if (!opts.file) {
    console.error('사용법: node scripts/load-acquisition-dates.mjs "References/도서 등록일.xlsx" [--dry-run]');
    process.exitCode = 1;
    return;
  }
  if (!fs.existsSync(opts.file)) throw new Error(`파일을 찾을 수 없습니다: ${opts.file}`);

  const rows = opts.file.toLowerCase().endsWith(".csv")
    ? parseCsv(fs.readFileSync(opts.file, "utf8"))
    : readXlsx(opts.file).rows;
  if (!rows.length) throw new Error("빈 파일입니다");

  const { periods, skipped } = parseRanges(rows);
  const check = validateRanges(periods);
  const gapsMissing = missingMonths(periods);

  console.log(`파일     : ${opts.file}`);
  console.log(`구간 수   : ${periods.length}${skipped.length ? ` (형식 오류로 제외 ${skipped.length}행)` : ""}`);
  console.log(`등록번호  : ${check.minNum} ~ ${check.maxNum}`);
  const years = [...new Set(periods.map((p) => p.year))].sort();
  console.log(`연도 범위 : ${years[0]} ~ ${years[years.length - 1]}`);

  if (check.issues.length) {
    console.log(`\n정합성 오류 ${check.issues.length}건 - 적재를 중단합니다:`);
    for (const i of check.issues.slice(0, 20)) console.log(`  [${i.kind}] ${i.detail}`);
    throw new Error("구간표 정합성 오류");
  }
  console.log("정합성   : 겹침 0 / 역전 0 / 시간순 단조 증가 확인");

  if (check.gaps.length) {
    const total = check.gaps.reduce((a, g) => a + g.count, 0);
    console.log(`번호 공백 : ${check.gaps.length}구간 ${total}번 (폐기·결번으로 생길 수 있어 오류는 아님)`);
  }
  if (gapsMissing.length) {
    console.log(`구간 없는 달: ${gapsMissing.join(", ")} (등록이 없던 달일 수 있음)`);
  }

  if (opts.dryRun) {
    console.log("\n--dry-run 이므로 DB에 쓰지 않고 종료합니다.");
    return { periods: periods.length, updated: 0, dryRun: true };
  }

  const pool = new Pool({
    host: DB_HOST, port: 5432, user: DB_USER,
    password: required("SUPABASE_DB_PASSWORD"),
    database: "postgres", ssl: { rejectUnauthorized: false }, max: 2,
  });
  const client = await pool.connect();

  try {
    const exists = await client.query("select to_regclass('public.book_registration_periods') as t");
    if (!exists.rows[0].t) {
      throw new Error("public.book_registration_periods 가 없습니다. db/acquisition_scoring.sql 을 먼저 적용하세요.");
    }

    await client.query("begin");

    // 구간표는 통째로 교체한다(부분 갱신 시 옛 구간이 남아 잘못 매칭될 수 있다).
    await client.query("truncate table public.book_registration_periods");
    const cols = ["year", "month", "half", "start_num", "end_num", "est_date"];
    const values = periods
      .map((_, r) => `(${cols.map((_, c) => `$${r * cols.length + c + 1}`).join(",")})`)
      .join(",");
    const params = periods.flatMap((p) => [p.year, p.month, p.half, p.startNum, p.endNum, p.estDate]);
    await client.query(
      `insert into public.book_registration_periods (${cols.join(",")}) values ${values}`,
      params,
    );

    // 구간에 걸리는 도서
    const matched = await client.query(
      `update public.books b
          set acquired_date = p.est_date,
              acquired_date_precision = 'half_month'
         from public.book_registration_periods p
        where public.reg_no_num(b.reg_no) between p.start_num and p.end_num`,
    );

    // 구간표 시작번호보다 앞선 도서 = 2019-01 이전 등록. 단일 대체값.
    const pre = await client.query(
      `update public.books b
          set acquired_date = $1::date,
              acquired_date_precision = 'pre_2019'
        where public.reg_no_num(b.reg_no) is not null
          and public.reg_no_num(b.reg_no) < $2
          and acquired_date_precision is distinct from 'half_month'`,
      [PRE_2019_DATE, check.minNum],
    );

    await client.query("commit");

    console.log(`\n구간표 적재 : ${periods.length}건`);
    console.log(`반월 추정   : ${matched.rowCount}권`);
    console.log(`2019년 이전 : ${pre.rowCount}권 (${PRE_2019_DATE} 대체값)`);

    const summary = await client.query(
      `select coalesce(acquired_date_precision, '(미배정)') as 정밀도,
              count(*)::int as 권수,
              min(acquired_date)::text as 최초, max(acquired_date)::text as 최종
         from public.books group by 1 order by 2 desc`,
    );
    console.table(summary.rows);

    if (opts.refresh) {
      console.log("통계 MV 갱신 중...");
      for (const mv of ["mv_book_usage", "mv_publisher_stats", "mv_author_stats", "mv_kdc_deficit"]) {
        try {
          await client.query(`refresh materialized view concurrently public.${mv}`);
        } catch (err) {
          console.log(`  ${mv}: concurrently 실패(${err.message}) → 일반 refresh`);
          await client.query(`refresh materialized view public.${mv}`);
        }
      }
      console.log("  완료");
    }

    return { periods: periods.length, updated: matched.rowCount + pre.rowCount, dryRun: false };
  } catch (err) {
    await client.query("rollback").catch(() => {});
    throw err;
  } finally {
    client.release();
    await pool.end();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  run().catch((err) => {
    console.error(`\n실패: ${err.message}`);
    process.exitCode = 1;
  });
}
