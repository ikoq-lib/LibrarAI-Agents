/**
 * SEOJI 종이책 신간 일일 수집기
 *
 * 국립중앙도서관 서지정보유통지원시스템(SEOJI)에서 새로 등록된 종이책을
 * public.book_catalog 에 증분 적재한다. B-01 수서 후보 풀의 원본이다.
 *
 * 증분 방식:
 *   start_input_date / end_input_date 파라미터는 API 가 무시한다(전체 140만 건이 그대로 나온다).
 *   그러나 sort=INPUT_DATE & order_by=DESC 정렬은 정상 동작하므로,
 *   등록일 역순 페이지를 워터마크에 도달할 때까지만 읽는 방식으로 증분 수집한다.
 *
 *   워터마크 = max(book_catalog.input_date) - LOOKBACK_DAYS
 *   같은 등록일 안의 정렬 순서는 요청마다 조금씩 달라 페이지 경계에서 중복이 생기지만,
 *   ea_isbn 기준 upsert 라 무해하다(실측 1000건 페이지당 20~40건 중복).
 *
 * 수집 대상:
 *   form=종이책 (API 단계 필터. 실측 1000/1000 이 종이책으로 확인됨)
 *   부가기호 코드표에서 collect=false 인 유형(중고교/초등 학습참고서, 전문서, 전자자료)은
 *   기본적으로 저장하지 않는다. SEOJI_STORE_EXCLUDED=1 로 저장할 수 있다.
 *
 * 사용법:
 *   node scripts/harvest-seoji-catalog.mjs                  증분 수집(기본)
 *   node scripts/harvest-seoji-catalog.mjs --dry-run        DB 쓰지 않고 수집만
 *   node scripts/harvest-seoji-catalog.mjs --days 30        최근 등록 30일치까지 소급
 *   node scripts/harvest-seoji-catalog.mjs --max-pages 200  페이지 상한 조정
 *
 * 환경변수:
 * - SEOJI_API_KEY_NL_DIRECT (필수)
 * - SUPABASE_DB_PASSWORD    (--dry-run 이 아니면 필수)
 * - SEOJI_LOOKBACK_DAYS     워터마크 안전 소급일 (기본 3)
 * - SEOJI_BOOTSTRAP_DAYS    최초 실행 시 소급일 (기본 30)
 * - SEOJI_MAX_PAGES         1회 실행 페이지 상한 (기본 60 = 6만 건)
 * - SEOJI_STORE_EXCLUDED    1이면 미수집 유형도 저장
 */
import pg from "pg";
import { pathToFileURL } from "node:url";

const { Pool } = pg;

const SEOJI_URL = "https://www.nl.go.kr/seoji/SearchApi.do";
const DB_HOST = "aws-0-ap-southeast-1.pooler.supabase.com";
const DB_USER = "postgres.tkyaganfdfiuesvbcbkr";

// API 상한은 1000. 초과하면 ERR_CODE 013 을 돌려준다.
const PAGE_SIZE = 1000;
const LOOKBACK_DAYS = Number(process.env.SEOJI_LOOKBACK_DAYS || 3);
const BOOTSTRAP_DAYS = Number(process.env.SEOJI_BOOTSTRAP_DAYS || 30);
const MAX_PAGES = Number(process.env.SEOJI_MAX_PAGES || 60);
const STORE_EXCLUDED = process.env.SEOJI_STORE_EXCLUDED === "1";
const REQUEST_TIMEOUT_MS = Number(process.env.SEOJI_TIMEOUT_MS || 30_000);
const REQUEST_GAP_MS = Number(process.env.SEOJI_REQUEST_GAP_MS || 300);

// ---------------------------------------------------------------------------
// 값 정규화
// ---------------------------------------------------------------------------

/** 'YYYYMMDD' -> 'YYYY-MM-DD'. 형식이 아니거나 달력에 없는 날짜면 null. */
export function toDate(v) {
  const s = String(v ?? "").trim();
  const m = s.match(/^(\d{4})(\d{2})(\d{2})$/);
  if (!m) return null;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
  const dt = new Date(Date.UTC(y, mo - 1, d));
  if (dt.getUTCMonth() + 1 !== mo || dt.getUTCDate() !== d) return null;
  return `${m[1]}-${m[2]}-${m[3]}`;
}

/** 가격/쪽수처럼 숫자만 의미 있는 값. 콤마·단위를 떼고 정수로. */
export function toInt(v) {
  const s = String(v ?? "").replace(/[^0-9]/g, "");
  if (!s) return null;
  const n = Number(s);
  return Number.isSafeInteger(n) ? n : null;
}

/** ISBN13 숫자 13자리만 통과시킨다. books.isbn 도 하이픈 없는 13자리라 그대로 대조된다. */
export function toIsbn13(v) {
  const s = String(v ?? "").replace(/[^0-9Xx]/g, "");
  return /^\d{13}$/.test(s) ? s : null;
}

export function toText(v) {
  const s = String(v ?? "").trim();
  return s === "" ? null : s;
}

/** 부가기호 5자리. 형식에 맞지 않으면 null(생성열 체크 제약을 통과시키기 위해). */
export function toAddCode(v) {
  const s = String(v ?? "").replace(/\s+/g, "");
  return /^\d{5}$/.test(s) ? s : null;
}

/**
 * SEOJI 레코드 -> book_catalog 행.
 * 권차는 SERIES_NO / SET_EXPRESSION / VOL 중 값이 있는 첫 항목을 쓴다(원본에 셋이 혼재).
 */
export function toCatalogRow(doc) {
  const eaIsbn = toIsbn13(doc.EA_ISBN);
  if (!eaIsbn) return null;
  const title = toText(doc.TITLE);
  if (!title) return null;

  return {
    ea_isbn: eaIsbn,
    set_isbn: toIsbn13(doc.SET_ISBN),
    title,
    author: toText(doc.AUTHOR),
    series_title: toText(doc.SERIES_TITLE),
    series_no: toText(doc.SERIES_NO) || toText(doc.SET_EXPRESSION) || toText(doc.VOL),
    edition_stmt: toText(doc.EDITION_STMT),
    publisher: toText(doc.PUBLISHER),
    publish_predate: toDate(doc.PUBLISH_PREDATE),
    input_date: toDate(doc.INPUT_DATE),
    pre_price: toInt(doc.PRE_PRICE),
    form_detail: toText(doc.FORM_DETAIL),
    page_count: toInt(doc.PAGE),
    book_size: toText(doc.BOOK_SIZE),
    ea_add_code: toAddCode(doc.EA_ADD_CODE),
  };
}

/** 'YYYY-MM-DD' 에서 n일 뺀 날짜. */
export function shiftDays(isoDate, n) {
  const t = Date.parse(`${isoDate}T00:00:00Z`);
  return new Date(t - n * 86_400_000).toISOString().slice(0, 10);
}

// ---------------------------------------------------------------------------
// SEOJI 호출
// ---------------------------------------------------------------------------

function required(name) {
  const v = process.env[name];
  if (!v) throw new Error(`환경변수 ${name} 가 필요합니다`);
  return v;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** 등록일 역순 한 페이지. 실패 시 최대 3회 재시도한다. */
export async function fetchPage(pageNo, certKey, fetchImpl = fetch, pageSize = PAGE_SIZE) {
  const params = new URLSearchParams({
    cert_key: certKey,
    result_style: "json",
    page_no: String(pageNo),
    page_size: String(pageSize),
    form: "종이책",
    sort: "INPUT_DATE",
    order_by: "DESC",
  });

  let lastErr;
  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      const ac = new AbortController();
      const timer = setTimeout(() => ac.abort(), REQUEST_TIMEOUT_MS);
      let text;
      try {
        const res = await fetchImpl(`${SEOJI_URL}?${params}`, { signal: ac.signal });
        text = await res.text();
      } finally {
        clearTimeout(timer);
      }
      if (!text || !text.trim()) throw new Error("빈 응답");

      const data = JSON.parse(text);
      if (data.RESULT === "ERROR") {
        throw new Error(`SEOJI 오류 ${data.ERR_CODE}: ${data.ERR_MESSAGE}`);
      }
      return { docs: data.docs || [], total: Number(data.TOTAL_COUNT || 0) };
    } catch (err) {
      lastErr = err;
      if (attempt < 3) await sleep(1000 * attempt);
    }
  }
  throw new Error(`페이지 ${pageNo} 수집 실패: ${lastErr.message}`);
}

/**
 * 워터마크에 도달할 때까지 등록일 역순으로 페이지를 읽는다.
 * 반환: { rows, pages, oldestInput, newestInput, total }
 */
export async function harvest({
  watermark, maxPages = MAX_PAGES, certKey,
  fetchImpl = fetch, log = console.log, pageSize = PAGE_SIZE,
}) {
  const byIsbn = new Map();
  let pages = 0;
  let total = 0;
  let oldestInput = null;
  let newestInput = null;
  let reachedWatermark = false;

  for (let page = 1; page <= maxPages; page++) {
    const { docs, total: t } = await fetchPage(page, certKey, fetchImpl, pageSize);
    pages = page;
    total = t;
    if (!docs.length) {
      log(`  page ${page}: 결과 없음 - 중단`);
      break;
    }

    let pageOldest = null;
    let pageNewest = null;
    for (const doc of docs) {
      const row = toCatalogRow(doc);
      if (!row) continue;
      if (row.input_date) {
        if (!pageOldest || row.input_date < pageOldest) pageOldest = row.input_date;
        if (!pageNewest || row.input_date > pageNewest) pageNewest = row.input_date;
      }
      // 페이지 경계 중복은 나중 값으로 덮어써도 무방하다(동일 레코드).
      byIsbn.set(row.ea_isbn, row);
    }

    if (pageOldest && (!oldestInput || pageOldest < oldestInput)) oldestInput = pageOldest;
    if (pageNewest && (!newestInput || pageNewest > newestInput)) newestInput = pageNewest;

    log(`  page ${page}: ${docs.length}건 (등록일 ${pageOldest} ~ ${pageNewest}, 누적 고유 ${byIsbn.size})`);

    if (watermark && pageOldest && pageOldest < watermark) {
      reachedWatermark = true;
      log(`  워터마크 ${watermark} 도달 - 수집 종료`);
      break;
    }
    // 페이지가 덜 찼다는 것은 마지막 페이지라는 뜻이다.
    if (docs.length < pageSize) break;
    await sleep(REQUEST_GAP_MS);
  }

  if (watermark && !reachedWatermark) {
    log(`  경고: 페이지 상한 ${maxPages} 에 걸려 워터마크까지 못 갔습니다. --max-pages 를 늘리거나 더 자주 실행하세요.`);
  }

  // 워터마크보다 오래된 레코드는 이미 적재돼 있으므로 버린다.
  const rows = [...byIsbn.values()].filter((r) => !watermark || !r.input_date || r.input_date >= watermark);
  return { rows, pages, oldestInput, newestInput, total, reachedWatermark };
}

// ---------------------------------------------------------------------------
// 적재
// ---------------------------------------------------------------------------

const COLUMNS = [
  "ea_isbn", "set_isbn", "title", "author", "series_title", "series_no",
  "edition_stmt", "publisher", "publish_predate", "input_date", "pre_price",
  "form_detail", "page_count", "book_size", "ea_add_code",
];

function chunk(list, size) {
  const out = [];
  for (let i = 0; i < list.length; i += size) out.push(list.slice(i, i + size));
  return out;
}

async function upsertRows(client, rows) {
  let affected = 0;
  for (const part of chunk(rows, 500)) {
    const values = part
      .map((_, r) => `(${COLUMNS.map((_, c) => `$${r * COLUMNS.length + c + 1}`).join(",")})`)
      .join(",");
    const params = part.flatMap((row) => COLUMNS.map((c) => row[c] ?? null));
    const res = await client.query(
      `insert into public.book_catalog (${COLUMNS.join(",")})
       values ${values}
       on conflict (ea_isbn) do update set
         set_isbn        = excluded.set_isbn,
         title           = excluded.title,
         author          = excluded.author,
         series_title    = excluded.series_title,
         series_no       = excluded.series_no,
         edition_stmt    = excluded.edition_stmt,
         publisher       = excluded.publisher,
         publish_predate = excluded.publish_predate,
         input_date      = excluded.input_date,
         pre_price       = excluded.pre_price,
         form_detail     = excluded.form_detail,
         page_count      = excluded.page_count,
         book_size       = excluded.book_size,
         ea_add_code     = excluded.ea_add_code,
         last_seen       = now()`,
      params,
    );
    affected += res.rowCount;
  }
  return affected;
}

/** 코드표의 collect=false 유형과 이미 소장 중인 책에 플래그를 세운다. */
async function markFlags(client) {
  const owned = await client.query(
    `update public.book_catalog bc set already_owned = true
      where already_owned = false
        and exists (select 1 from public.books b where b.isbn = bc.ea_isbn)`,
  );
  const audience = await client.query(
    `update public.book_catalog bc
        set excluded = true,
            exclude_reason = '독자대상 미수집(' || a.label || ')'
       from public.add_code_audience a
      where a.code = bc.add_code_audience and a.collect = false and bc.excluded = false`,
  );
  const form = await client.query(
    `update public.book_catalog bc
        set excluded = true,
            exclude_reason = '발행형태 미수집(' || f.label || ')'
       from public.add_code_form f
      where f.code = bc.add_code_form and f.collect = false and bc.excluded = false`,
  );
  return { owned: owned.rowCount, audience: audience.rowCount, form: form.rowCount };
}

/** 저장 전 단계에서 미수집 유형을 걸러낸다(코드표를 DB에서 읽어 적용). */
export function applyCollectFilter(rows, audienceSkip, formSkip) {
  const kept = [];
  const skipped = [];
  for (const row of rows) {
    const a = row.ea_add_code ? row.ea_add_code[0] : null;
    const f = row.ea_add_code ? row.ea_add_code[1] : null;
    if ((a && audienceSkip.has(a)) || (f && formSkip.has(f))) skipped.push(row);
    else kept.push(row);
  }
  return { kept, skipped };
}

function parseArgs(argv) {
  const opts = { dryRun: false, days: null, maxPages: MAX_PAGES, refresh: true };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dry-run") opts.dryRun = true;
    else if (a === "--no-refresh") opts.refresh = false;
    else if (a === "--days") opts.days = Number(argv[++i]);
    else if (a === "--max-pages") opts.maxPages = Number(argv[++i]);
  }
  return opts;
}

export async function run(argv = process.argv.slice(2)) {
  const opts = parseArgs(argv);
  const certKey = required("SEOJI_API_KEY_NL_DIRECT");
  const today = new Date().toISOString().slice(0, 10);

  let pool;
  let client;
  let watermark = null;
  let audienceSkip = new Set();
  let formSkip = new Set();

  // --dry-run 도 DB 를 읽는다(워터마크·코드표). 쓰기만 하지 않는다.
  const canConnect = Boolean(process.env.SUPABASE_DB_PASSWORD);
  if (!opts.dryRun && !canConnect) required("SUPABASE_DB_PASSWORD");

  if (canConnect) {
    pool = new Pool({
      host: DB_HOST, port: 5432, user: DB_USER,
      password: required("SUPABASE_DB_PASSWORD"),
      database: "postgres", ssl: { rejectUnauthorized: false }, max: 2,
    });
    client = await pool.connect();

    const exists = await client.query("select to_regclass('public.book_catalog') as t");
    if (!exists.rows[0].t) {
      throw new Error("public.book_catalog 이 없습니다. db/acquisition_scoring.sql 을 먼저 적용하세요.");
    }

    const mark = await client.query("select max(input_date)::text as m, count(*)::int n from public.book_catalog");
    const { m, n } = mark.rows[0];
    if (opts.days != null) {
      watermark = shiftDays(today, opts.days);
      console.log(`소급 수집: 등록일 ${watermark} 이후 (--days ${opts.days})`);
    } else if (opts.dryRun && !m) {
      watermark = shiftDays(today, 2);
      console.log(`--dry-run: 등록일 ${watermark} 이후만 확인합니다.`);
    } else if (m) {
      watermark = shiftDays(m, LOOKBACK_DAYS);
      console.log(`증분 수집: 최신 등록일 ${m}, 워터마크 ${watermark} (안전 소급 ${LOOKBACK_DAYS}일)`);
    } else {
      watermark = shiftDays(today, BOOTSTRAP_DAYS);
      console.log(`최초 수집: 등록일 ${watermark} 이후 (부트스트랩 ${BOOTSTRAP_DAYS}일)`);
    }
    console.log(`기존 적재 ${n}건`);

    if (!STORE_EXCLUDED) {
      const a = await client.query("select code from public.add_code_audience where collect = false");
      const f = await client.query("select code from public.add_code_form where collect = false");
      audienceSkip = new Set(a.rows.map((r) => r.code));
      formSkip = new Set(f.rows.map((r) => r.code));
    }
    if (opts.dryRun) console.log("--dry-run: DB 에는 쓰지 않습니다.");
  } else {
    watermark = shiftDays(today, opts.days ?? 2);
    console.log(`--dry-run(DB 미접속): 등록일 ${watermark} 이후만 수집합니다.`);
  }

  try {
    console.log("");
    const result = await harvest({ watermark, maxPages: opts.maxPages, certKey });
    console.log("");
    console.log(`수집 페이지 : ${result.pages} (SEOJI 전체 ${result.total.toLocaleString()}건)`);
    console.log(`등록일 범위 : ${result.oldestInput} ~ ${result.newestInput}`);
    console.log(`워터마크 이후 고유 레코드: ${result.rows.length}건`);

    if (!result.rows.length) {
      console.log("새로 등록된 종이책이 없습니다.");
      return { stored: 0, skipped: 0, ...result };
    }

    const { kept, skipped } = STORE_EXCLUDED
      ? { kept: result.rows, skipped: [] }
      : applyCollectFilter(result.rows, audienceSkip, formSkip);
    if (skipped.length) {
      console.log(`미수집 유형 제외: ${skipped.length}건 (학습참고서·전문서·전자자료 등)`);
    }

    if (opts.dryRun) {
      console.log(`\n--dry-run 이므로 저장하지 않습니다. 저장 대상 ${kept.length}건`);
      const sample = kept.slice(0, 5).map((r) => `  ${r.publish_predate ?? "발행일미상"} | ${r.ea_add_code ?? "-----"} | ${r.publisher ?? "?"} | ${r.title}`);
      console.log(sample.join("\n"));
      return { stored: 0, skipped: skipped.length, ...result };
    }

    await client.query("begin");
    const affected = await upsertRows(client, kept);
    const flags = await markFlags(client);
    await client.query("commit");

    console.log(`\n적재 완료: ${affected}건 upsert`);
    console.log(`  이미 소장으로 표시 : ${flags.owned}건`);
    console.log(`  독자대상 제외 표시 : ${flags.audience}건`);
    console.log(`  발행형태 제외 표시 : ${flags.form}건`);

    const summary = await client.query(
      `select count(*)::int 전체,
              count(*) filter (where not excluded and not already_owned)::int 유효후보,
              min(input_date)::text 최초등록일,
              max(input_date)::text 최종등록일
         from public.book_catalog`,
    );
    console.table(summary.rows);

    if (opts.refresh) {
      // book_catalog 자체는 통계 MV 의 원본이 아니라 갱신이 필수는 아니지만,
      // 장서/대출이 바뀐 날에도 점수가 최신이도록 함께 돌린다.
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

    const top = await client.query(
      `select left(title, 40) as 제목, publisher as 출판사, 대상, 주제, score_total as 총점
         from public.v_candidate_scores
        where not excluded and not already_owned
        order by score_total desc limit 5`,
    );
    if (top.rows.length) {
      console.log("\n현재 점수 상위 5종:");
      console.table(top.rows);
    }

    return { stored: affected, skipped: skipped.length, ...result };
  } catch (err) {
    if (client) await client.query("rollback").catch(() => {});
    throw err;
  } finally {
    if (client) client.release();
    if (pool) await pool.end();
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] || "").href) {
  run().catch((err) => {
    console.error(`\n실패: ${err.message}`);
    process.exitCode = 1;
  });
}
