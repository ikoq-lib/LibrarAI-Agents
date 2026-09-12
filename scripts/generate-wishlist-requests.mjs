/**
 * B-02 희망도서 주간 신청 생성기
 *
 * 연구용 데모 환경에는 홈페이지 신청 폼이 없다. 그래서 주 1회(화요일 새벽) 이 봇이
 * SEOJI 일일 수집분(public.book_catalog)에서 발행 30일이 지난 책을 무작위로 뽑아
 * 직전 월~일 접수분으로 신청 건을 만든다. B-02 는 화요일에 그 주차를 처리한다.
 *
 * 설계 결정(2026-09-12 사서 확인):
 *   - 가중치 없음. 정기수서(B-01)와 달리 점수·균형·출판사 실적을 보지 않는다.
 *     이용자 신청은 그런 축과 무관하게 흩어지므로 가중치가 오히려 분포를 왜곡한다.
 *   - 반려 대상을 미리 걸러내지 않는다. 수험서·5만원 초과·부적합 제본·5년 초과가
 *     자연 비율(모수의 6% 남짓)로 섞여 들어와야 B-02 의 R-01~R-10 판정이 일한다.
 *   - 신청자는 고정 풀에서 재사용한다. 매주 새 이름을 만들면 한 사람이 한 주에
 *     한 번만 등장해 FN-04(1인 월 3권 한도)가 항상 통과해 검증이 무의미해진다.
 *
 * 사용법:
 *   node scripts/generate-wishlist-requests.mjs               직전 주차 생성
 *   node scripts/generate-wishlist-requests.mjs --dry-run     DB 쓰지 않고 미리보기
 *   node scripts/generate-wishlist-requests.mjs --week 2026-09-07   특정 주차(월요일)
 *   node scripts/generate-wishlist-requests.mjs --count 30    생성 권수 고정
 *   node scripts/generate-wishlist-requests.mjs --seed 42     난수 고정(재현용)
 *   node scripts/generate-wishlist-requests.mjs --force       이미 있는 주차를 지우고 재생성
 *
 * 환경변수:
 * - SUPABASE_DB_PASSWORD    (--dry-run 이 아니면 필수)
 * - WISHLIST_MIN_BOOKS      주당 최소 권수 (기본 20)
 * - WISHLIST_MAX_BOOKS      주당 최대 권수 (기본 30)
 * - WISHLIST_PATRON_POOL    신청자 풀 크기 (기본 40)
 * - WISHLIST_AGE_DAYS       발행 후 경과일 하한 (기본 30)
 */
import pg from "pg";
import { pathToFileURL } from "node:url";

const { Pool } = pg;

const DB_HOST = "aws-0-ap-southeast-1.pooler.supabase.com";
const DB_USER = "postgres.tkyaganfdfiuesvbcbkr";

const MIN_BOOKS = Number(process.env.WISHLIST_MIN_BOOKS || 20);
const MAX_BOOKS = Number(process.env.WISHLIST_MAX_BOOKS || 30);
const PATRON_POOL = Number(process.env.WISHLIST_PATRON_POOL || 40);
const AGE_DAYS = Number(process.env.WISHLIST_AGE_DAYS || 30);

// 한 사람이 한 주에 신청하는 권수 상한. 월 3권 한도(FN-04)는 주 단위가 아니라
// 월 단위 규정이므로, 주당 3권까지 허용하면 월 3권 초과가 자연스럽게 발생한다.
const MAX_BOOKS_PER_PATRON_PER_WEEK = 3;

// 연령 구성. 수서 계획 산정 기준(성인50·청소년10·어린이25·유아15)을 신청자 분포에도 쓴다.
const AGE_BANDS = [
  { group: "성인",   weight: 50, min: 19, max: 75 },
  { group: "어린이", weight: 25, min: 8,  max: 13 },
  { group: "유아",   weight: 15, min: 4,  max: 7 },
  { group: "청소년", weight: 10, min: 14, max: 18 },
];

// ---------------------------------------------------------------------------
// 난수 — --seed 로 고정할 수 있어야 테스트에서 결과를 재현한다.
// ---------------------------------------------------------------------------

/** mulberry32. 시드 하나로 재현 가능한 난수열을 만든다. */
export function makeRng(seed) {
  let a = (seed >>> 0) || 1;
  return function next() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 0 이상 n 미만의 정수. */
function randInt(rng, n) {
  return Math.floor(rng() * n);
}

/** min 이상 max 이하의 정수. */
function randBetween(rng, min, max) {
  return min + randInt(rng, max - min + 1);
}

/** Fisher-Yates. 원본을 건드리지 않고 섞은 새 배열을 돌려준다. */
export function shuffle(list, rng) {
  const out = [...list];
  for (let i = out.length - 1; i > 0; i--) {
    const j = randInt(rng, i + 1);
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

/** weight 에 비례해 하나를 고른다. */
function pickWeighted(bands, rng) {
  const total = bands.reduce((s, b) => s + b.weight, 0);
  let r = rng() * total;
  for (const b of bands) {
    r -= b.weight;
    if (r <= 0) return b;
  }
  return bands[bands.length - 1];
}

// ---------------------------------------------------------------------------
// 주차 계산
// ---------------------------------------------------------------------------

/** 'YYYY-MM-DD' 를 UTC 자정 Date 로. 로컬 타임존이 날짜를 밀지 않게 UTC 로 고정한다. */
export function parseDate(s) {
  const m = String(s ?? "").match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const d = new Date(Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3])));
  return Number.isNaN(d.getTime()) ? null : d;
}

export function fmtDate(d) {
  return d.toISOString().slice(0, 10);
}

export function addDays(d, n) {
  return new Date(d.getTime() + n * 86400000);
}

/**
 * 기준일이 속한 주의 월요일. getUTCDay 는 일요일이 0 이라 일요일을 전주로 보내야 한다.
 * (월~일 접수 사이클이므로 일요일은 그 주의 마지막 날이다.)
 */
export function mondayOf(date) {
  const dow = date.getUTCDay();
  const back = dow === 0 ? 6 : dow - 1;
  return addDays(date, -back);
}

/**
 * 화요일 새벽에 돌면서 "직전에 접수가 끝난 월~일"을 고른다.
 * 화요일 기준 이번 주 월요일은 어제라 아직 접수가 끝나지 않았으므로 한 주 앞으로 간다.
 */
export function targetWeek(today) {
  return addDays(mondayOf(today), -7);
}

/** ISO 8601 주차 번호. 주간 보고 머리말("YYYY년 N주차")에 쓴다. */
export function isoWeekNo(monday) {
  const d = new Date(monday.getTime());
  d.setUTCDate(d.getUTCDate() + 3); // 그 주 목요일이 속한 해가 ISO 기준 연도다.
  const year = d.getUTCFullYear();
  const jan4 = new Date(Date.UTC(year, 0, 4));
  const week1Monday = mondayOf(jan4);
  return { year, week: Math.round((d.getTime() - week1Monday.getTime()) / (7 * 86400000)) + 1 };
}

/**
 * 접수 시각을 주 안에 흩는다. 개관 시간(09~21시) 안으로 넣고, 주말 신청도 허용한다.
 * KST 기준 시각을 만들어야 하므로 UTC 로는 9시간을 뺀다.
 */
export function randomRequestedAt(monday, rng) {
  const dayOffset = randInt(rng, 7);
  const hourKst = randBetween(rng, 9, 21);
  const minute = randInt(rng, 60);
  const base = addDays(monday, dayOffset);
  return new Date(Date.UTC(
    base.getUTCFullYear(), base.getUTCMonth(), base.getUTCDate(),
    hourKst - 9, minute, randInt(rng, 60),
  ));
}

// ---------------------------------------------------------------------------
// 신청자 풀
// ---------------------------------------------------------------------------

/** 풀에 모자란 인원을 채울 신규 신청자를 만든다. 이름은 테스트N 으로 이어 붙인다. */
export function buildPatrons(existingCount, targetCount, rng) {
  const out = [];
  for (let i = existingCount + 1; i <= targetCount; i++) {
    const band = pickWeighted(AGE_BANDS, rng);
    out.push({
      name: `테스트${i}`,
      age: randBetween(rng, band.min, band.max),
      age_group: band.group,
      gender: rng() < 0.5 ? "남" : "여",
    });
  }
  return out;
}

/**
 * 한 신청자가 한 번에 몇 권을 신청할지. 순환 배정으로 전원에게 1권씩 나눠주면
 * 주 단위 분포가 부자연스럽다 — 실제 이용자는 한 번에 2~3권을 몰아 신청한다.
 */
export function pickRequestSize(rng, maxPerPatron = MAX_BOOKS_PER_PATRON_PER_WEEK) {
  const r = rng();
  const size = r < 0.6 ? 1 : r < 0.9 ? 2 : 3;
  return Math.min(size, maxPerPatron);
}

/**
 * 책을 신청자에게 배정한다. 신청자 순서를 섞은 뒤 앞에서부터 1~3권씩 묶어 넘기므로
 * 매주 등장하는 얼굴이 달라지고, 한 사람이 여러 권을 신청한 주도 생긴다.
 * 한 주 상한은 3권이지만 FN-04 한도는 월 3권이라, 여러 주가 쌓이면 초과가 발생한다.
 */
export function assignPatrons(books, patrons, rng, maxPerPatron = MAX_BOOKS_PER_PATRON_PER_WEEK) {
  if (!patrons.length) throw new Error("신청자 풀이 비어 있습니다.");
  const capacity = patrons.length * maxPerPatron;
  if (books.length > capacity) {
    throw new Error(`신청자 풀이 부족합니다: ${books.length}권 / 최대 ${capacity}권(${patrons.length}명 × ${maxPerPatron}권)`);
  }

  const order = shuffle(patrons, rng);
  const counts = new Map();
  const out = [];
  let cursor = 0;
  let i = 0;

  while (i < books.length) {
    // 이번 주 상한에 찬 사람은 건너뛰고 다음 여유 있는 신청자를 찾는다.
    let picked = null;
    for (let g = 0; g < order.length; g++) {
      const p = order[(cursor + g) % order.length];
      if ((counts.get(p.id) ?? 0) < maxPerPatron) {
        picked = p;
        cursor = (cursor + g + 1) % order.length;
        break;
      }
    }
    if (!picked) throw new Error(`신청자 풀이 부족합니다: ${books.length}권 / 최대 ${capacity}권`);

    const room = maxPerPatron - (counts.get(picked.id) ?? 0);
    const take = Math.min(pickRequestSize(rng, maxPerPatron), room, books.length - i);
    counts.set(picked.id, (counts.get(picked.id) ?? 0) + take);
    for (let k = 0; k < take; k++) out.push({ book: books[i++], patron: picked });
  }
  return out;
}

// ---------------------------------------------------------------------------
// DB
// ---------------------------------------------------------------------------

const REQUEST_COLUMNS = [
  "request_week", "requested_at", "patron_id",
  "ea_isbn", "title", "author", "publisher", "pre_price", "form_detail",
  "source",
];

async function ensurePatronPool(client, rng, poolSize) {
  const { rows } = await client.query(
    "select id, name, age, age_group, gender from public.wishlist_patrons where is_mock order by id",
  );
  if (rows.length >= poolSize) return { patrons: rows, added: 0 };

  const fresh = buildPatrons(rows.length, poolSize, rng);
  const values = fresh
    .map((_, i) => `($${i * 4 + 1},$${i * 4 + 2},$${i * 4 + 3},$${i * 4 + 4})`)
    .join(",");
  const params = fresh.flatMap((p) => [p.name, p.age, p.age_group, p.gender]);
  const inserted = await client.query(
    `insert into public.wishlist_patrons (name, age, age_group, gender)
     values ${values}
     on conflict (name) do nothing
     returning id, name, age, age_group, gender`,
    params,
  );
  return { patrons: [...rows, ...inserted.rows], added: inserted.rowCount };
}

/**
 * 후보를 뽑는다. 발행 30일 경과 + 아직 신청된 적 없는 책.
 * 정렬 없이 random() 으로 섞는다 — 가중치를 두지 않기로 한 결정이 여기에 있다.
 */
async function pickBooks(client, count, ageDays) {
  const { rows } = await client.query(
    `select ea_isbn, title, author, publisher, pre_price, form_detail
       from public.book_catalog bc
      where bc.publish_predate is not null
        and bc.publish_predate <= current_date - $2::int
        and not exists (select 1 from public.wishlist_requests r where r.ea_isbn = bc.ea_isbn)
      order by random()
      limit $1`,
    [count, ageDays],
  );
  return rows;
}

async function insertRequests(client, week, pairs, rng) {
  const rows = pairs.map(({ book, patron }) => ({
    request_week: week,
    requested_at: randomRequestedAt(parseDate(week), rng).toISOString(),
    patron_id: patron.id,
    ea_isbn: book.ea_isbn,
    title: book.title,
    author: book.author,
    publisher: book.publisher,
    pre_price: book.pre_price,
    form_detail: book.form_detail,
    source: "mock",
  }));

  const values = rows
    .map((_, r) => `(${REQUEST_COLUMNS.map((_, c) => `$${r * REQUEST_COLUMNS.length + c + 1}`).join(",")})`)
    .join(",");
  const params = rows.flatMap((row) => REQUEST_COLUMNS.map((c) => row[c] ?? null));
  const res = await client.query(
    `insert into public.wishlist_requests (${REQUEST_COLUMNS.join(",")})
     values ${values}
     on conflict (request_week, patron_id, ea_isbn) do nothing`,
    params,
  );
  return res.rowCount;
}

function parseArgs(argv) {
  const opts = { dryRun: false, week: null, count: null, seed: null, force: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--dry-run") opts.dryRun = true;
    else if (a === "--force") opts.force = true;
    else if (a === "--week") opts.week = argv[++i];
    else if (a === "--count") opts.count = Number(argv[++i]);
    else if (a === "--seed") opts.seed = Number(argv[++i]);
  }
  return opts;
}

function required(name) {
  const v = process.env[name];
  if (!v) throw new Error(`환경변수 ${name} 가 필요합니다.`);
  return v;
}

export async function run(argv = process.argv.slice(2)) {
  const opts = parseArgs(argv);
  const rng = makeRng(opts.seed ?? Date.now());

  const today = new Date();
  const week = opts.week ? parseDate(opts.week) : targetWeek(today);
  if (!week) throw new Error(`--week 는 YYYY-MM-DD(월요일) 형식이어야 합니다: ${opts.week}`);
  if (week.getUTCDay() !== 1) {
    throw new Error(`--week 는 월요일이어야 합니다: ${fmtDate(week)} (${["일","월","화","수","목","금","토"][week.getUTCDay()]}요일)`);
  }
  const weekStr = fmtDate(week);
  const { year, week: weekNo } = isoWeekNo(week);
  const count = opts.count ?? randBetween(rng, MIN_BOOKS, MAX_BOOKS);

  console.log(`대상 주차 : ${year}년 ${weekNo}주차 (${weekStr} ~ ${fmtDate(addDays(week, 6))})`);
  console.log(`생성 권수 : ${count}권 (범위 ${MIN_BOOKS}~${MAX_BOOKS})`);

  if (!opts.dryRun) required("SUPABASE_DB_PASSWORD");
  if (opts.dryRun && !process.env.SUPABASE_DB_PASSWORD) {
    throw new Error("--dry-run 도 후보 조회를 위해 SUPABASE_DB_PASSWORD 가 필요합니다.");
  }

  const pool = new Pool({
    host: DB_HOST, port: 5432, user: DB_USER,
    password: required("SUPABASE_DB_PASSWORD"),
    database: "postgres", ssl: { rejectUnauthorized: false }, max: 2,
  });
  const client = await pool.connect();

  try {
    const exists = await client.query("select to_regclass('public.wishlist_requests') as t");
    if (!exists.rows[0].t) {
      throw new Error("public.wishlist_requests 가 없습니다. db/wishlist_requests.sql 을 먼저 적용하세요.");
    }

    const dup = await client.query(
      "select count(*)::int n from public.wishlist_requests where request_week = $1",
      [weekStr],
    );
    if (dup.rows[0].n > 0) {
      if (!opts.force) {
        console.log(`\n${weekStr} 주차에 이미 ${dup.rows[0].n}건이 있습니다. 재생성하려면 --force 를 쓰세요.`);
        return { created: 0, week: weekStr, skipped: true };
      }
      if (!opts.dryRun) {
        const del = await client.query(
          "delete from public.wishlist_requests where request_week = $1 and source = 'mock'",
          [weekStr],
        );
        console.log(`--force: 기존 목업 ${del.rowCount}건 삭제(실제 신청분은 보존)`);
      }
    }

    const { patrons, added } = opts.dryRun
      ? { patrons: (await client.query("select id, name, age, age_group, gender from public.wishlist_patrons where is_mock order by id")).rows, added: 0 }
      : await ensurePatronPool(client, rng, PATRON_POOL);
    if (added) console.log(`신청자 풀 : ${added}명 신규 등록 (총 ${patrons.length}명)`);
    else console.log(`신청자 풀 : ${patrons.length}명`);

    if (!patrons.length) {
      throw new Error("신청자 풀이 비어 있습니다. --dry-run 없이 한 번 실행해 풀을 만드세요.");
    }

    const books = await pickBooks(client, count, AGE_DAYS);
    console.log(`후보 조회 : ${books.length}권 (발행 ${AGE_DAYS}일 경과 · 미신청)`);
    if (books.length < count) {
      console.log(`  경고: 요청 ${count}권보다 적습니다. 미신청 후보가 소진돼 갑니다.`);
    }
    if (!books.length) {
      console.log("생성할 신청 건이 없습니다.");
      return { created: 0, week: weekStr, skipped: false };
    }

    const pairs = assignPatrons(books, patrons, rng);

    if (opts.dryRun) {
      console.log(`\n--dry-run 이므로 저장하지 않습니다. 생성 대상 ${pairs.length}건`);
      for (const { book, patron } of pairs.slice(0, 8)) {
        const price = book.pre_price ? `${book.pre_price.toLocaleString()}원` : "가격미상";
        console.log(`  ${patron.name}(${patron.age}세 ${patron.gender}) | ${book.title} | ${book.publisher ?? "?"} | ${price} | ${book.form_detail ?? "-"}`);
      }
      if (pairs.length > 8) console.log(`  ... 외 ${pairs.length - 8}건`);
      return { created: 0, week: weekStr, pairs: pairs.length, skipped: false };
    }

    await client.query("begin");
    const created = await insertRequests(client, weekStr, pairs, rng);
    await client.query("commit");

    console.log(`\n생성 완료: ${created}건`);

    const summary = await client.query(
      `select 신청건수, 신청자수, 미처리 from public.v_wishlist_weekly where request_week = $1`,
      [weekStr],
    );
    console.table(summary.rows);

    const over = await client.query(
      `select 신청자, age_group as 연령대, 신청권수
         from public.v_wishlist_monthly_quota
        where 한도초과 and 신청월 = date_trunc('month', $1::date)::date
        order by 신청권수 desc limit 10`,
      [weekStr],
    );
    if (over.rows.length) {
      console.log(`\n이번 달 1인 3권 한도 초과(FN-04 판정 대상) ${over.rows.length}명:`);
      console.table(over.rows);
    }

    return { created, week: weekStr, skipped: false };
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
