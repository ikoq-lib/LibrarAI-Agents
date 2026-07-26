/**
 * B-01 주간 추천도서 취합기
 *
 * 출처별 공개 페이지를 먼저 직접 수집하고, 직접 수집이 불가능하거나 할당량에
 * 못 미친 출처만 OpenRouter 웹 검색으로 보완한다. SEOJI는 후보 발굴원이
 * 아니라 실존·서지·포맷을 확인하는 베스트에포트 검증원이다.
 *
 * 운영 환경변수:
 * - OPENROUTER_API_KEY: AI 보완 수집이 필요할 때
 * - SEOJI_API_KEY_NL_DIRECT: SEOJI 검증을 사용할 때
 * - SUPABASE_DB_PASSWORD: 후보 풀에 적재할 때
 *
 * 로컬 진단:
 * - B01_HARVEST_SKIP_AI=1
 * - B01_HARVEST_SKIP_SEOJI=1
 * - B01_HARVEST_SKIP_DB=1
 */
import * as cheerio from "cheerio";
import pdfParse from "pdf-parse/lib/pdf-parse.js";
import pg from "pg";
import { pathToFileURL } from "node:url";

const { Pool } = pg;

const OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions";
const SEOJI_URL = "https://www.nl.go.kr/seoji/SearchApi.do";
const MODEL = process.env.B01_HARVEST_MODEL || "google/gemini-3.5-flash";
const USER_AGENT =
  "Mozilla/5.0 (compatible; LibrarAI-B01/1.0; +https://github.com/ikoq-lib/LibrarAI-Agents)";
const REQUEST_TIMEOUT_MS = Number(process.env.B01_HARVEST_TIMEOUT_MS || 30_000);
const MIN_SUCCESS = Number(process.env.B01_HARVEST_MIN_SUCCESS || 40);
const PARTIAL_SUCCESS = Number(process.env.B01_HARVEST_PARTIAL_SUCCESS || 30);
const MAX_STORED = Number(process.env.B01_HARVEST_MAX_STORED || 50);
const SKIP_AI = process.env.B01_HARVEST_SKIP_AI === "1";
const SKIP_SEOJI = process.env.B01_HARVEST_SKIP_SEOJI === "1";
const SKIP_DB = process.env.B01_HARVEST_SKIP_DB === "1";
const ALLOWED_FORM_DETAILS = new Set(["무선제본", "양장본", "보드북"]);

export const SOURCES = [
  {
    id: "kpipa",
    label: "출판유통통합전산망 화제의 책 200선",
    cap: 20,
    domain: "bnk.kpipa.or.kr",
    collector: collectKpipa,
  },
  {
    id: "kyobo",
    label: "교보문고",
    cap: 15,
    domain: "product.kyobobook.co.kr",
  },
  {
    id: "yes24",
    label: "YES24",
    cap: 15,
    domain: "yes24.com",
    collector: collectYes24,
  },
  {
    id: "hani",
    label: "한겨레 책과 생각",
    cap: 5,
    domain: "hani.co.kr",
  },
  {
    id: "donga",
    label: "동아일보 금주의 신간",
    cap: 5,
    domain: "donga.com",
  },
  {
    id: "nlk",
    label: "국립중앙도서관 사서추천도서",
    cap: 5,
    domain: "nl.go.kr",
    collector: collectNlk,
  },
  {
    id: "nlcy",
    label: "국립어린이청소년도서관 사서추천도서",
    cap: 5,
    domain: "nlcy.go.kr",
    collector: collectNlcy,
  },
  {
    id: "data4library",
    label: "도서관 정보나루 인기대출도서",
    cap: 5,
    domain: "data4library.kr",
  },
];

const RESERVE_SOURCES = [
  { id: "aladin", label: "알라딘", domain: "aladin.co.kr", cap: 10 },
  { id: "ypbooks", label: "영풍문고", domain: "ypbooks.co.kr", cap: 10 },
];

function required(name) {
  const value = process.env[name];
  if (!value) throw new Error(`${name} 환경변수가 필요합니다.`);
  return value;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function fetchWithRetry(url, options = {}, attempts = 3) {
  let lastError;
  for (let attempt = 1; attempt <= attempts; attempt += 1) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          "User-Agent": USER_AGENT,
          "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5",
          ...(options.headers || {}),
        },
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${(await response.text()).slice(0, 180)}`);
      }
      return response;
    } catch (error) {
      lastError = error;
      if (attempt < attempts) await sleep(500 * 2 ** (attempt - 1));
    } finally {
      clearTimeout(timeout);
    }
  }
  throw lastError;
}

function cleanText(value = "") {
  return String(value).replace(/\s+/g, " ").trim();
}

export function normalizeIsbn(value = "") {
  return String(value).replace(/[^0-9Xx]/g, "").toUpperCase();
}

function normalizeDate(value = "") {
  const digits = String(value).replace(/[^0-9]/g, "");
  return digits.length >= 8 ? digits.slice(0, 8) : digits;
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

function candidateFor(source, fields) {
  return {
    title: cleanText(fields.title),
    author: cleanText(fields.author),
    publisher: cleanText(fields.publisher),
    isbn: /^\d{13}$/.test(normalizeIsbn(fields.isbn)) ? normalizeIsbn(fields.isbn) : "",
    pubdate: normalizeDate(fields.pubdate),
    genre: cleanText(fields.genre),
    sources: [source.label],
    source_urls: [...new Set([fields.source_url].filter(Boolean))],
    popnote: cleanText(fields.popnote || `${source.label} 수록`),
    collection_method: fields.collection_method || "direct",
  };
}

export function parseYes24Html(html, source = SOURCES.find((item) => item.id === "yes24")) {
  const $ = cheerio.load(html);
  const rows = [];
  $("li .itemUnit").each((_, element) => {
    const item = $(element);
    const link = item.find("a.gd_name").first();
    const href = link.attr("href");
    const priceText = item.find(".info_price").first().text();
    rows.push(
      candidateFor(source, {
        title: link.attr("title") || link.text(),
        author: item.find(".info_auth").first().text().replace(/\s*저\s*$/, ""),
        publisher: item.find(".info_pub").first().text(),
        source_url: href ? new URL(href, "https://www.yes24.com").href : source.url,
        popnote: cleanText(`YES24 신상품 ${priceText}`),
      }),
    );
  });
  return rows.filter((item) => item.title).slice(0, source.cap);
}

async function collectYes24(source) {
  const url = "https://www.yes24.com/Product/Category/NewProduct?categoryNumber=001";
  const html = await (await fetchWithRetry(url)).text();
  return parseYes24Html(html, { ...source, url });
}

export function parseNlkHtml(html, source = SOURCES.find((item) => item.id === "nlk")) {
  const $ = cheerio.load(html);
  const rows = [];
  $("li.uccst14_item").each((_, element) => {
    const item = $(element);
    const title = item.find("strong.title").first();
    const detailHref = item.find("a[href]").first().attr("href");
    rows.push(
      candidateFor(source, {
        title: title.attr("title") || title.text(),
        author: item.find("dd.author").first().text(),
        publisher: item.find("dd.publisher").first().text(),
        pubdate: item.find("dd.year").first().text(),
        genre: item.find(".category").first().text(),
        source_url: detailHref ? new URL(detailHref, "https://www.nl.go.kr").href : source.url,
        popnote: `국립중앙도서관 ${cleanText(item.find(".date").first().text())} 사서추천`,
      }),
    );
  });
  return rows.filter((item) => item.title).slice(0, source.cap);
}

async function collectNlk(source) {
  const url = "https://www.nl.go.kr/NL/contents/N20500000000.do";
  const html = await (await fetchWithRetry(url)).text();
  return parseNlkHtml(html, { ...source, url });
}

export function parseNlcyHtml(html, source = SOURCES.find((item) => item.id === "nlcy")) {
  const $ = cheerio.load(html);
  const rows = [];
  const seen = new Set();

  $("[class*=book], [class*=recommend], li, article").each((_, element) => {
    const item = $(element);
    const text = cleanText(item.text());
    if (!text.includes("추천사서") || !text.includes("도서정보")) return;
    const image = item.find("img[alt]").first();
    const title =
      cleanText(image.attr("alt")).replace(/\s*\(\d{4}년\s*\d{1,2}월\s*추천도서\)\s*$/, "") ||
      cleanText(item.find("strong, .title").first().text());
    if (!title || seen.has(normalizeKey(title))) return;
    const infoMatch = text.match(/도서정보\s*(.+?)(?:\s*책소개|\s*자료상세보기|$)/);
    const info = infoMatch?.[1] || "";
    const parts = info.split("|").map(cleanText);
    rows.push(
      candidateFor(source, {
        title,
        author: parts[0],
        publisher: parts[1],
        pubdate: parts[2],
        genre: text.match(/주제구분\s*([^\s]+)/)?.[1] || "어린이·청소년",
        source_url: source.url,
        popnote: `국립어린이청소년도서관 사서추천`,
      }),
    );
    seen.add(normalizeKey(title));
  });

  // 페이지 개편으로 컨테이너 클래스가 바뀐 경우 이미지 alt를 안전한 최소 정보로 사용한다.
  if (rows.length === 0) {
    $("img[alt*='추천도서']").each((_, element) => {
      const image = $(element);
      const title = cleanText(image.attr("alt")).replace(/\s*\(\d{4}년\s*\d{1,2}월\s*추천도서\)\s*$/, "");
      if (!title || seen.has(normalizeKey(title))) return;
      rows.push(
        candidateFor(source, {
          title,
          genre: "어린이·청소년",
          source_url: source.url,
          popnote: "국립어린이청소년도서관 사서추천",
        }),
      );
      seen.add(normalizeKey(title));
    });
  }
  return rows.slice(0, source.cap);
}

async function collectNlcy(source) {
  const url = "https://www.nlcy.go.kr/NLCY/contents/C10600000000.do";
  const html = await (await fetchWithRetry(url)).text();
  return parseNlcyHtml(html, { ...source, url });
}

export function parseKpipaPdfText(text, source = SOURCES.find((item) => item.id === "kpipa"), sourceUrl = "") {
  const rows = [];
  for (const line of String(text).split(/\r?\n/)) {
    const match = line.match(/^\s*(\d{1,3})\s*(.+?)(97[89]\d{10})(.*)$/);
    if (!match) continue;
    const [, rank, rawTitle, isbn, remainder] = match;
    const title = cleanText(rawTitle);
    if (!title || Number(rank) > 200) continue;
    if (/수능|기출문제|평가문제집|자습서|토익|쎈\s|오투중등|개뿔중학|디딤돌 초등/.test(title)) continue;
    rows.push(
      candidateFor(source, {
        title,
        isbn,
        source_url: sourceUrl,
        popnote: `출판유통통합전산망 화제의 책 ${rank}위${cleanText(remainder) ? ` · ${cleanText(remainder)}` : ""}`,
      }),
    );
  }
  return rows.slice(0, source.cap);
}

async function collectKpipa(source) {
  const listUrl = "https://bnk.kpipa.or.kr/home/v3/helpdesk/hlpBbsNoticeBoardList";
  const listHtml = await (await fetchWithRetry(listUrl)).text();
  const $ = cheerio.load(listHtml);
  let sequence = "";
  $(".board-list-item").each((_, element) => {
    if (sequence) return;
    const item = $(element);
    if (!/화제의 책\s*200선/.test(cleanText(item.text()))) return;
    sequence = item.attr("onclick")?.match(/fnBbsNoticeBoardDetailView\('([^']+)'/)?.[1] || "";
  });
  if (!sequence) throw new Error("최신 '화제의 책 200선' 공지를 찾지 못했습니다.");

  const detailUrl =
    `https://bnk.kpipa.or.kr/home/v3/helpdesk/hlpBbsNoticeBoardDetailView/seq_${sequence}`;
  const detailHtml = await (await fetchWithRetry(detailUrl)).text();
  const pdfPath =
    detailHtml.match(/['"]([^'"]+\.pdf)['"]/i)?.[1] ||
    detailHtml.match(/(\/files\/board\/[^"'<> ]+\.pdf)/i)?.[1];
  if (!pdfPath) throw new Error("화제의 책 PDF 첨부파일을 찾지 못했습니다.");
  const pdfUrl = new URL(pdfPath, "https://bnk.kpipa.or.kr").href;
  const buffer = Buffer.from(await (await fetchWithRetry(pdfUrl)).arrayBuffer());
  const parsed = await pdfParse(buffer);
  return parseKpipaPdfText(parsed.text, { ...source, url: detailUrl }, pdfUrl);
}

export function parseAiDiscovery(text, source, limit = source.cap) {
  const content = String(text || "").replace(/```(?:json)?|```/gi, "").trim();
  const start = content.indexOf("[");
  const end = content.lastIndexOf("]");
  let parsed = [];
  if (start >= 0 && end > start) {
    try {
      parsed = JSON.parse(content.slice(start, end + 1));
    } catch {
      // 웹 검색 모델이 인용 표기를 섞은 경우 아래 파이프 형식으로 한 번 더 읽는다.
    }
  }
  if (!Array.isArray(parsed) || parsed.length === 0) {
    parsed = content
      .split(/\r?\n/)
      .map((line) => line.replace(/^[\s\-*\d.)]+/, "").trim())
      .filter((line) => line.includes("|"))
      .map((line) => {
        const [title, author, publisher, isbn, pubdate, genre, source_url, ...reason] =
          line.split("|").map(cleanText);
        return { title, author, publisher, isbn, pubdate, genre, source_url, reason: reason.join(" | ") };
      })
      .filter((item) => item.title && !/^(제목|title)$/i.test(item.title));
  }
  if (!Array.isArray(parsed) || parsed.length === 0) {
    throw new Error(`AI 보완 결과를 해석하지 못했습니다: ${content.slice(0, 220)}`);
  }
  return parsed
    .map((item) => {
      let sourceUrl = "";
      try {
        const parsedUrl = new URL(item.source_url);
        const hostname = parsedUrl.hostname.toLowerCase();
        if (hostname === source.domain || hostname.endsWith(`.${source.domain}`)) {
          sourceUrl = parsedUrl.href;
        }
      } catch {
        // 지정 출처 URL이 확인되지 않은 항목은 아래 filter에서 제외한다.
      }
      return candidateFor(source, {
        title: item.title,
        author: item.author,
        publisher: item.publisher,
        isbn: item.isbn,
        pubdate: item.pubdate,
        genre: item.genre,
        source_url: sourceUrl,
        popnote: item.reason || `${source.label} 수록`,
        collection_method: "ai_web_fallback",
      });
    })
    .filter((item) => item.title && item.source_urls.length > 0)
    .slice(0, limit);
}

async function discoverSourceWithAi(source, limit) {
  if (SKIP_AI || limit <= 0) return [];
  const system = [
    "너는 한국 공공도서관 수서 사서 보조다.",
    "지정된 출처의 실제 공개 페이지만 웹 검색하고, 거기에 명시된 국내 종이책만 반환한다.",
    "책 제목·ISBN을 추측하거나 다른 출처의 책을 섞지 않는다.",
    "전자책·외국서적·학술보고서·정부간행물·자가출판·세트·정가 5만원 이상은 제외한다.",
    "설명 없이 JSON 배열만 출력한다.",
  ].join(" ");
  const user = [
    `출처: ${source.label}`,
    `검색 허용 도메인: ${source.domain}`,
    `목표: 최신 신간·추천·인기대출 도서 중 서로 다른 책 최대 ${limit}종`,
    "언론사는 기사 제목이 아니라 기사에서 실제로 소개한 책을 추출한다.",
    "우선 JSON 배열로 출력한다. 웹 인용 때문에 JSON 출력이 불가능하면 아래 8개 필드를 파이프(|)로 구분해 책마다 한 줄로 출력한다.",
    "각 항목 JSON 형식:",
    '{"title":"","author":"","publisher":"","isbn":"","pubdate":"YYYY-MM-DD","genre":"","source_url":"","reason":""}',
    "파이프 형식: 제목 | 저자 | 출판사 | ISBN13 | 출간일 | 분야 | 지정 출처의 실제 URL | 수록 근거",
  ].join("\n");
  let lastError;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const response = await fetchWithRetry(
        OPENROUTER_URL,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${required("OPENROUTER_API_KEY")}`,
            "HTTP-Referer": "https://librar-ai-agents.vercel.app",
            "X-Title": "LibrarAI B-01 Source Harvester",
          },
          body: JSON.stringify({
            model: MODEL,
            temperature: 0.1,
            max_tokens: 3000,
            reasoning: { effort: "low" },
            stream: false,
            tools: [
              {
                type: "openrouter:web_search",
                parameters: {
                  engine: "exa",
                  max_results: Math.min(10, Math.max(5, limit)),
                  max_characters: 3000,
                  allowed_domains: [source.domain],
                },
              },
            ],
            messages: [
              { role: "system", content: system },
              { role: "user", content: user },
            ],
          }),
        },
        1,
      );
      const data = await response.json();
      return parseAiDiscovery(data.choices?.[0]?.message?.content || "", source, limit);
    } catch (error) {
      lastError = error;
      if (attempt < 3) await sleep(750 * 2 ** (attempt - 1));
    }
  }
  throw lastError;
}

async function collectSource(source) {
  let direct = [];
  let directError = "";
  if (source.collector) {
    try {
      direct = await source.collector(source);
    } catch (error) {
      directError = error.message;
      console.warn(`${source.label} 직접 수집 실패: ${error.message}`);
    }
  }
  const directMerged = mergeCandidates(direct).slice(0, source.cap);
  let fallback = [];
  const missing = source.cap - directMerged.length;
  if (missing > 0 && !SKIP_AI) {
    try {
      fallback = await discoverSourceWithAi(source, missing);
    } catch (error) {
      console.warn(`${source.label} AI 보완 실패: ${error.message}`);
    }
  }
  const candidates = mergeCandidates([...directMerged, ...fallback]).slice(0, source.cap);
  return {
    source,
    candidates,
    direct: directMerged.length,
    ai_fallback: Math.max(0, candidates.length - directMerged.length),
    direct_error: directError || null,
  };
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

  const response = await fetchWithRetry(`${SEOJI_URL}?${params.toString()}`, {}, 3);
  const data = await response.json();
  const docs = Array.isArray(data.docs) ? data.docs : [];
  const doc = candidate.isbn
    ? docs.find((item) => normalizeIsbn(item.EA_ISBN) === normalizeIsbn(candidate.isbn))
    : docs.find((item) => normalizeKey(item.TITLE) === normalizeKey(candidate.title));
  if (!doc) return candidate;

  const ebookYn = String(doc.EBOOK_YN || "").trim().toUpperCase();
  const form = String(doc.FORM || "").trim();
  const formDetail = String(doc.FORM_DETAIL || "").trim();
  if (ebookYn === "Y" || (form && form !== "종이책")) return null;
  if (formDetail && !ALLOWED_FORM_DETAILS.has(formDetail)) return null;
  if (/세트|전\s*\d+\s*권/.test(doc.TITLE || candidate.title)) return null;

  const priceRaw = String(doc.PRE_PRICE || "").replace(/[^0-9]/g, "");
  const price = priceRaw ? Number(priceRaw) : null;
  if (price && price >= 50_000) return null;
  const isbn = normalizeIsbn(doc.EA_ISBN || candidate.isbn);
  return {
    ...candidate,
    isbn: /^\d{13}$/.test(isbn) ? isbn : candidate.isbn,
    title: cleanText(doc.TITLE || candidate.title),
    author: cleanText(doc.AUTHOR || candidate.author),
    publisher: cleanText(doc.PUBLISHER || candidate.publisher),
    pubdate: normalizeDate(doc.PUBLISH_PREDATE || doc.REAL_PUBLISH_DATE || candidate.pubdate),
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

export function mergeCandidates(candidates) {
  const byKey = new Map();
  for (const candidate of candidates.filter(Boolean)) {
    const key = dedupKey(candidate);
    if (!candidate.title || key === "title:|") continue;
    const existing = byKey.get(key);
    if (!existing) {
      byKey.set(key, {
        ...candidate,
        dedup_key: key,
        sources: [...new Set(candidate.sources || [])],
        source_urls: [...new Set(candidate.source_urls || [])],
      });
      continue;
    }
    existing.sources = [...new Set([...(existing.sources || []), ...(candidate.sources || [])])];
    existing.source_urls = [...new Set([...(existing.source_urls || []), ...(candidate.source_urls || [])])];
    existing.popnote = [...new Set([existing.popnote, candidate.popnote].filter(Boolean))].join(" / ");
    if (!existing.isbn && candidate.isbn) existing.isbn = candidate.isbn;
    if (!existing.author && candidate.author) existing.author = candidate.author;
    if (!existing.publisher && candidate.publisher) existing.publisher = candidate.publisher;
  }
  return [...byKey.values()];
}

function rankCandidates(candidates) {
  return [...candidates].sort((a, b) => {
    const sourceDifference = (b.sources?.length || 0) - (a.sources?.length || 0);
    if (sourceDifference) return sourceDifference;
    const verifiedDifference = Number(Boolean(b.verified)) - Number(Boolean(a.verified));
    if (verifiedDifference) return verifiedDifference;
    return String(b.pubdate || "").localeCompare(String(a.pubdate || ""));
  });
}

export function selectFinalCandidates(candidates, max = MAX_STORED) {
  const ranked = rankCandidates(candidates);
  const selected = [];
  const selectedKeys = new Set();
  const orderedSources = [...SOURCES, ...RESERVE_SOURCES];
  const queues = orderedSources.map((source) => ({
    source,
    items: ranked.filter((candidate) => candidate.sources?.includes(source.label)),
    cursor: 0,
  }));

  // 출처별로 한 종씩 순환해 소수 할당 언론·공공기관 출처가 잘리지 않게 한다.
  while (selected.length < max) {
    let addedThisRound = false;
    for (const queue of queues) {
      while (queue.cursor < queue.items.length) {
        const candidate = queue.items[queue.cursor++];
        const key = dedupKey(candidate);
        if (selectedKeys.has(key)) continue;
        selected.push(candidate);
        selectedKeys.add(key);
        addedThisRound = true;
        break;
      }
      if (selected.length >= max) break;
    }
    if (!addedThisRound) break;
  }

  for (const candidate of ranked) {
    if (selected.length >= max) break;
    const key = dedupKey(candidate);
    if (selectedKeys.has(key)) continue;
    selected.push(candidate);
    selectedKeys.add(key);
  }
  return selected;
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
      create index if not exists acq_cand_status_idx on public.acquisition_candidates (status);
      create index if not exists acq_cand_pubdate_idx on public.acquisition_candidates (pubdate);
      create index if not exists acq_cand_verified_idx on public.acquisition_candidates (verified);
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
          JSON.stringify({
            harvested_at: new Date().toISOString(),
            model: MODEL,
            source_urls: candidate.source_urls || [],
            collection_method: candidate.collection_method || "direct",
          }),
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
  if (!SKIP_DB) required("SUPABASE_DB_PASSWORD");
  if (!SKIP_SEOJI) required("SEOJI_API_KEY_NL_DIRECT");

  const results = await mapLimited(SOURCES, 4, collectSource);
  const discovered = results.flatMap((result) => result.candidates);
  let merged = mergeCandidates(discovered);

  // 1차 출처에서 40종 미만이면 서점 예비 출처만 필요한 만큼 보완한다.
  const reserveResults = [];
  if (merged.length < MIN_SUCCESS && !SKIP_AI) {
    for (const reserve of RESERVE_SOURCES) {
      const needed = Math.min(reserve.cap, MIN_SUCCESS - merged.length);
      if (needed <= 0) break;
      try {
        const candidates = await discoverSourceWithAi(reserve, needed);
        reserveResults.push({
          source: reserve,
          candidates,
          direct: 0,
          ai_fallback: candidates.length,
          direct_error: null,
        });
        merged = mergeCandidates([...merged, ...candidates]);
      } catch (error) {
        console.warn(`${reserve.label} 예비 수집 실패: ${error.message}`);
      }
    }
  }

  const enriched = SKIP_SEOJI ? merged : await mapLimited(merged, 4, seojiLookup);
  const finalCandidates = selectFinalCandidates(mergeCandidates(enriched.filter(Boolean)), MAX_STORED);
  if (!SKIP_DB) await upsertCandidates(finalCandidates);

  const verified = finalCandidates.filter((candidate) => candidate.verified).length;
  const allResults = [...results, ...reserveResults];
  const summary = {
    harvested_at: new Date().toISOString(),
    target: `${MIN_SUCCESS}-${MAX_STORED}`,
    raw_discovered: discovered.length + reserveResults.flatMap((item) => item.candidates).length,
    deduplicated: merged.length,
    stored: finalCandidates.length,
    seoji_verified: verified,
    unverified: finalCandidates.length - verified,
    source_coverage: allResults.filter((item) => item.candidates.length > 0).length,
    sources: Object.fromEntries(
      allResults.map((item) => [
        item.source.id,
        {
          target: item.source.cap,
          collected: item.candidates.length,
          direct: item.direct,
          ai_fallback: item.ai_fallback,
          direct_error: item.direct_error,
        },
      ]),
    ),
    dry_run: SKIP_DB,
  };
  console.log(JSON.stringify(summary, null, 2));

  if (finalCandidates.length < PARTIAL_SUCCESS) {
    throw new Error(
      `후보가 ${finalCandidates.length}종으로 실패 기준 ${PARTIAL_SUCCESS}종에 미달했습니다. ` +
      "출처별 오류와 OpenRouter 크레딧을 확인하세요.",
    );
  }
  if (finalCandidates.length < MIN_SUCCESS) {
    console.warn(
      `::warning::후보가 ${finalCandidates.length}종으로 부분 성공입니다. 목표 최소 ${MIN_SUCCESS}종에 미달했습니다.`,
    );
  }
}

const entryUrl = process.argv[1] ? pathToFileURL(process.argv[1]).href : "";
if (import.meta.url === entryUrl) {
  main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
  });
}
