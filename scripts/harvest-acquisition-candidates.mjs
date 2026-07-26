/**
 * B-01 주간 추천도서 취합기
 *
 * 여러 장르의 국내 신간·화제 도서를 웹 검색으로 발굴하고, SEOJI로 서지를
 * 베스트에포트 검증한 뒤 public.acquisition_candidates에 누적한다.
 *
 * 필수 환경변수:
 * - OPENROUTER_API_KEY
 * - SUPABASE_DB_PASSWORD
 * - SEOJI_API_KEY_NL_DIRECT
 */
import pg from "pg";

const { Pool } = pg;

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const SEOJI_URL = "https://www.nl.go.kr/seoji/SearchApi.do";
const MODEL = process.env.B01_HARVEST_MODEL || "google/gemini-3.5-flash";
const GENRE_CAP = Number(process.env.B01_HARVEST_GENRE_CAP || 12);
const GENRES = [
  "소설·문학·시",
  "에세이·인문·역사",
  "자기계발·실용·경제경영",
  "과학·기술·교양",
  "어린이·청소년",
  "예술·취미·생활·건강",
];
const ALLOWED_FORM_DETAILS = new Set(["무선제본", "양장본", "보드북"]);

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} 환경변수가 필요합니다.`);
  return value;
}

function normalizeIsbn(value = "") {
  return String(value).replace(/[^0-9Xx]/g, "").toUpperCase();
}

function normalizeKey(value = "") {
  return String(value)
    .normalize("NFKC")
    .replace(/[\s·:：,，.\-—~()[\]『』「」'"!?]/g, "")
    .toLowerCase();
}

function dedupKey(candidate) {
  const isbn = normalizeIsbn(candidate.isbn);
  return /^\d{13}$/.test(isbn)
    ? `isbn:${isbn}`
    : `title:${normalizeKey(candidate.title)}|${normalizeKey(candidate.author)}`;
}

function parseDiscovery(text, genre) {
  const rows = [];
  for (const sourceLine of String(text || "").split("\n")) {
    const line = sourceLine.replace(/^[\s\-*\d.)]+/, "").trim();
    if (!line.includes("|")) continue;
    const parts = line.split("|").map((part) => part.trim());
    const [title, author, publisher, isbnRaw, pubdateRaw, sourcesRaw, ...noteParts] = parts;
    if (!title || /^(제목|title)$/i.test(title)) continue;
    const isbn = normalizeIsbn(isbnRaw);
    rows.push({
      title,
      author: author && author !== "미상" ? author : "",
      publisher: publisher && publisher !== "미상" ? publisher : "",
      isbn: /^\d{13}$/.test(isbn) ? isbn : "",
      pubdate: pubdateRaw && pubdateRaw !== "미상" ? pubdateRaw.replace(/[^0-9]/g, "") : "",
      genre,
      sources: (sourcesRaw || "")
        .split(/[,;/·]/)
        .map((value) => value.trim())
        .filter((value) => value && value !== "미상"),
      popnote: noteParts.join(" | ").trim(),
    });
  }
  return rows.slice(0, GENRE_CAP);
}

async function discoverGenre(genre) {
  const system = [
    "너는 공공도서관 수서 사서 보조다.",
    "웹 검색으로 실제 출간이 확인된 국내 신간만 제시한다.",
    "서점 베스트셀러·출판사 신간·언론 서평·공공기관 추천·북튜버 및 독서 인플루언서 추천을 고르게 탐색한다.",
    "존재가 불확실한 책이나 학술보고서·논문·정부간행물·자가출판·전자책·외국서적은 넣지 않는다.",
    "각 도서를 정확히 한 줄로, 필드는 파이프(|)로 구분하고 다른 설명은 쓰지 않는다.",
  ].join(" ");
  const user = [
    `최근 6개월에 국내 출간된 ${genre} 분야의 대중적으로 인기 있거나 화제성이 높은 일반 단행본을 최대 ${GENRE_CAP}종 찾아라.`,
    "동일한 도서를 여러 곳이 추천했다면 실제 매체·채널·서점·출판사 이름을 모두 적어라.",
    "ISBN은 검색 중 확인된 13자리만 쓰고 확실하지 않으면 미상으로 둔다. 추측하지 않는다.",
    "형식:",
    "제목 | 저자 | 출판사 | ISBN13(모르면 미상) | 출간일 YYYY-MM-DD(모르면 미상) | 추천출처명(쉼표 구분) | 인기·추천 근거 한 구절",
  ].join("\n");

  const response = await fetch(OPENROUTER_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${required("OPENROUTER_API_KEY")}`,
      "HTTP-Referer": "https://librar-ai-agents.vercel.app",
      "X-Title": "LibrarAI B-01 Weekly Harvester",
    },
    body: JSON.stringify({
      model: MODEL,
      temperature: 0.3,
      // OpenRouter는 잔여 크레딧을 max_tokens 기준으로 선승인한다. 실제 12종 한 줄 목록은
      // 1,800토큰이면 충분하며, 상한을 크게 잡으면 내용 생성 전 HTTP 402가 날 수 있다.
      max_tokens: 1800,
      stream: false,
      plugins: [{ id: "web", engine: "native" }],
      messages: [
        { role: "system", content: system },
        { role: "user", content: user },
      ],
    }),
  });
  const body = await response.text();
  if (!response.ok) throw new Error(`${genre} 발굴 실패(HTTP ${response.status}): ${body.slice(0, 300)}`);
  const data = JSON.parse(body);
  return parseDiscovery(data.choices?.[0]?.message?.content || "", genre);
}

async function seojiLookup(candidate) {
  const params = new URLSearchParams({
    cert_key: required("SEOJI_API_KEY_NL_DIRECT"),
    result_style: "json",
    page_no: "1",
    page_size: candidate.isbn ? "5" : "10",
  });
  if (candidate.isbn) params.set("isbn", candidate.isbn);
  else params.set("title", candidate.title);

  const response = await fetch(`${SEOJI_URL}?${params.toString()}`);
  if (!response.ok) return candidate;
  const data = await response.json();
  const docs = Array.isArray(data.docs) ? data.docs : [];
  const doc = candidate.isbn
    ? docs.find((item) => normalizeIsbn(item.EA_ISBN) === candidate.isbn)
    : docs.find((item) => normalizeKey(item.TITLE) === normalizeKey(candidate.title));
  if (!doc) return candidate;

  const ebookYn = String(doc.EBOOK_YN || "").trim().toUpperCase();
  const form = String(doc.FORM || "").trim();
  const formDetail = String(doc.FORM_DETAIL || "").trim();
  if (ebookYn === "Y" || (form && form !== "종이책")) return null;
  if (formDetail && !ALLOWED_FORM_DETAILS.has(formDetail)) return null;
  if (/세트|전\s*\d+\s*권/.test(doc.TITLE || candidate.title)) return null;

  const isbn = normalizeIsbn(doc.EA_ISBN || candidate.isbn);
  const priceRaw = String(doc.PRE_PRICE || "").replace(/[^0-9]/g, "");
  const price = priceRaw ? Number(priceRaw) : null;
  if (price && price >= 50000) return null;
  return {
    ...candidate,
    isbn: /^\d{13}$/.test(isbn) ? isbn : candidate.isbn,
    title: String(doc.TITLE || candidate.title).trim(),
    author: String(doc.AUTHOR || candidate.author || "").trim(),
    publisher: String(doc.PUBLISHER || candidate.publisher || "").trim(),
    pubdate: String(doc.PUBLISH_PREDATE || doc.REAL_PUBLISH_DATE || candidate.pubdate || "").replace(/[^0-9]/g, ""),
    price,
    formDetail,
    verified: true,
  };
}

async function mapLimited(items, limit, mapper) {
  const results = new Array(items.length);
  let cursor = 0;
  async function worker() {
    while (cursor < items.length) {
      const index = cursor++;
      try {
        results[index] = await mapper(items[index], index);
      } catch (error) {
        console.warn(`항목 ${index + 1} 보강 실패: ${error.message}`);
        results[index] = items[index];
      }
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return results;
}

function mergeCandidates(candidates) {
  const byKey = new Map();
  for (const candidate of candidates.filter(Boolean)) {
    const key = dedupKey(candidate);
    if (!candidate.title || key === "title:|") continue;
    const existing = byKey.get(key);
    if (!existing) {
      byKey.set(key, { ...candidate, dedup_key: key, sources: [...new Set(candidate.sources || [])] });
      continue;
    }
    existing.sources = [...new Set([...(existing.sources || []), ...(candidate.sources || [])])];
    existing.popnote = [existing.popnote, candidate.popnote].filter(Boolean).join(" / ");
    if (!existing.isbn && candidate.isbn) existing.isbn = candidate.isbn;
  }
  return [...byKey.values()];
}

async function upsertCandidates(candidates) {
  const pool = new Pool({
    host: "aws-0-ap-southeast-1.pooler.supabase.com",
    port: 5432,
    user: "postgres.tkyaganfdfiuesvbcbkr",
    password: required("SUPABASE_DB_PASSWORD"),
    database: "postgres",
    ssl: { rejectUnauthorized: false },
    max: 2,
  });
  const client = await pool.connect();
  try {
    await client.query("begin");
    // 배포 환경에 마이그레이션이 아직 적용되지 않았어도 첫 실행이 스스로 복구되도록 한다.
    // 모두 IF NOT EXISTS/멱등 구문이라 이후 주간 실행에서는 기존 테이블을 그대로 사용한다.
    await client.query(`
      create table if not exists public.acquisition_candidates (
        id bigint generated always as identity primary key,
        dedup_key text not null unique,
        isbn text,
        title text not null,
        author text,
        publisher text,
        pubdate text,
        price integer,
        form_detail text,
        genre text,
        sources text[] not null default '{}',
        recommend_count integer not null default 1,
        popnote text,
        verified boolean not null default false,
        status text not null default 'candidate',
        first_seen timestamptz not null default now(),
        last_seen timestamptz not null default now(),
        metadata jsonb not null default '{}'::jsonb
      );
      create index if not exists acq_cand_status_idx
        on public.acquisition_candidates (status);
      create index if not exists acq_cand_pubdate_idx
        on public.acquisition_candidates (pubdate);
      create index if not exists acq_cand_verified_idx
        on public.acquisition_candidates (verified);
      create unique index if not exists acq_cand_isbn_uidx
        on public.acquisition_candidates (isbn) where isbn is not null;
      alter table public.acquisition_candidates enable row level security;
      drop policy if exists "acq_cand public read" on public.acquisition_candidates;
      create policy "acq_cand public read"
        on public.acquisition_candidates for select using (true);
    `);
    for (const candidate of candidates) {
      await client.query(
        `insert into public.acquisition_candidates
           (dedup_key, isbn, title, author, publisher, pubdate, price, form_detail,
            genre, sources, recommend_count, popnote, verified, status, last_seen, metadata)
         values
           ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::text[], $11, $12, $13,
            'candidate', now(), $14::jsonb)
         on conflict (dedup_key) do update set
           isbn = coalesce(excluded.isbn, acquisition_candidates.isbn),
           title = excluded.title,
           author = coalesce(excluded.author, acquisition_candidates.author),
           publisher = coalesce(excluded.publisher, acquisition_candidates.publisher),
           pubdate = coalesce(excluded.pubdate, acquisition_candidates.pubdate),
           price = coalesce(excluded.price, acquisition_candidates.price),
           form_detail = coalesce(excluded.form_detail, acquisition_candidates.form_detail),
           genre = coalesce(excluded.genre, acquisition_candidates.genre),
           sources = (select array_agg(distinct value)
                        from unnest(acquisition_candidates.sources || excluded.sources) as value),
           recommend_count = greatest(
             acquisition_candidates.recommend_count,
             cardinality((select array_agg(distinct value)
                           from unnest(acquisition_candidates.sources || excluded.sources) as value))
           ),
           popnote = case
             when acquisition_candidates.popnote is null then excluded.popnote
             when excluded.popnote is null then acquisition_candidates.popnote
             when acquisition_candidates.popnote like '%' || excluded.popnote || '%' then acquisition_candidates.popnote
             else acquisition_candidates.popnote || ' / ' || excluded.popnote
           end,
           verified = acquisition_candidates.verified or excluded.verified,
           last_seen = now(),
           metadata = acquisition_candidates.metadata || excluded.metadata`,
        [
          candidate.dedup_key,
          candidate.isbn || null,
          candidate.title,
          candidate.author || null,
          candidate.publisher || null,
          candidate.pubdate || null,
          candidate.price || null,
          candidate.formDetail || null,
          candidate.genre || null,
          candidate.sources || [],
          Math.max(1, (candidate.sources || []).length),
          candidate.popnote || null,
          Boolean(candidate.verified),
          JSON.stringify({ harvested_at: new Date().toISOString(), model: MODEL }),
        ],
      );
    }
    await client.query("commit");
  } catch (error) {
    await client.query("rollback");
    throw error;
  } finally {
    client.release();
    await pool.end();
  }
}

async function main() {
  required("OPENROUTER_API_KEY");
  required("SEOJI_API_KEY_NL_DIRECT");
  required("SUPABASE_DB_PASSWORD");

  const discovered = [];
  for (let index = 0; index < GENRES.length; index += 2) {
    const pair = GENRES.slice(index, index + 2);
    const results = await Promise.allSettled(pair.map(discoverGenre));
    results.forEach((result, pairIndex) => {
      if (result.status === "fulfilled") discovered.push(...result.value);
      else console.warn(`${pair[pairIndex]} 발굴 실패: ${result.reason?.message || result.reason}`);
    });
  }

  const merged = mergeCandidates(discovered);
  const enriched = await mapLimited(merged, 2, seojiLookup);
  const finalCandidates = mergeCandidates(enriched.filter(Boolean));
  await upsertCandidates(finalCandidates);

  const verified = finalCandidates.filter((candidate) => candidate.verified).length;
  console.log(JSON.stringify({
    harvested_at: new Date().toISOString(),
    discovered: discovered.length,
    deduplicated: merged.length,
    stored: finalCandidates.length,
    seoji_verified: verified,
    unverified: finalCandidates.length - verified,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
