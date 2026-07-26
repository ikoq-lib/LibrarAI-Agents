import test from "node:test";
import assert from "node:assert/strict";

import {
  SOURCES,
  mergeCandidates,
  parseAiDiscovery,
  parseKpipaPdfText,
  parseNlcyHtml,
  parseNlkHtml,
  parseYes24Html,
  selectFinalCandidates,
} from "../scripts/harvest-acquisition-candidates.mjs";

test("YES24 신상품 HTML에서 제목·저자·출판사를 읽는다", () => {
  const html = `
    <li><div class="itemUnit">
      <a class="gd_name" href="/Product/Goods/1" title="테스트 책">테스트 책</a>
      <span class="info_auth">홍길동 저</span>
      <span class="info_pub">테스트출판사</span>
      <span class="info_price">18,000원</span>
    </div></li>`;
  const [book] = parseYes24Html(html);
  assert.equal(book.title, "테스트 책");
  assert.equal(book.author, "홍길동");
  assert.equal(book.publisher, "테스트출판사");
  assert.equal(book.sources[0], "YES24");
});

test("국립중앙도서관 추천 HTML에서 서지 항목을 읽는다", () => {
  const html = `
    <li class="uccst14_item">
      <span class="date">2026. 7.</span><span class="category">인문</span>
      <strong class="title" title="추천 책">추천 책</strong>
      <dl><dd class="author">김사서</dd><dd class="publisher">책마을</dd>
      <dd class="year">2026</dd></dl>
    </li>`;
  const [book] = parseNlkHtml(html);
  assert.equal(book.title, "추천 책");
  assert.equal(book.pubdate, "2026");
  assert.equal(book.genre, "인문");
});

test("국립어린이청소년도서관 추천 HTML의 도서정보를 읽는다", () => {
  const html = `
    <article class="recommend-book">
      <img alt="어린이 추천 책 (2026년 7월 추천도서)">
      <div>주제구분 문학 추천사서 김사서
      도서정보 글: 이작가 ; 그림: 박화가 | 어린이책방 | 2026
      책소개 즐거운 책이다.</div>
    </article>`;
  const [book] = parseNlcyHtml(html);
  assert.equal(book.title, "어린이 추천 책");
  assert.equal(book.author, "글: 이작가 ; 그림: 박화가");
  assert.equal(book.publisher, "어린이책방");
});

test("출판유통통합전산망 PDF 행에서 순위·제목·ISBN을 읽는다", () => {
  const text = "1  프로젝트 헤일메리9788925588735 앤디 위어 알에이치코리아 22000 2026-01-02";
  const [book] = parseKpipaPdfText(text);
  assert.equal(book.title, "프로젝트 헤일메리");
  assert.equal(book.isbn, "9788925588735");
  assert.match(book.popnote, /1위/);
});

test("AI 보완 JSON은 출처와 수집 방식을 보존한다", () => {
  const source = SOURCES.find((item) => item.id === "kyobo");
  const [book] = parseAiDiscovery(
    '```json\n[{"title":"교보 추천 책","author":"이저자","source_url":"https://product.kyobobook.co.kr/detail/1"}]\n```',
    source,
  );
  assert.equal(book.sources[0], "교보문고");
  assert.equal(book.collection_method, "ai_web_fallback");
});

test("AI 보완 결과는 지정 출처 도메인의 근거 URL이 있어야 한다", () => {
  const source = SOURCES.find((item) => item.id === "donga");
  const books = parseAiDiscovery(
    '[{"title":"허용 책","source_url":"https://www.donga.com/news/Culture/article/1"},' +
      '{"title":"다른 출처 책","source_url":"https://example.com/book/2"}]',
    source,
  );
  assert.deepEqual(books.map((book) => book.title), ["허용 책"]);
});

test("웹 검색 응답의 파이프 형식도 보완 후보로 읽는다", () => {
  const source = SOURCES.find((item) => item.id === "hani");
  const [book] = parseAiDiscovery(
    "1. 파이프 책 | 박저자 | 책출판 | 9781234567890 | 2026-07-01 | 인문 | " +
      "https://www.hani.co.kr/arti/culture/book/1 | 책과 생각 소개",
    source,
  );
  assert.equal(book.title, "파이프 책");
  assert.equal(book.isbn, "9781234567890");
  assert.equal(book.collection_method, "ai_web_fallback");
});

test("ISBN 중복 후보는 출처와 URL을 합친다", () => {
  const merged = mergeCandidates([
    {
      title: "같은 책",
      isbn: "9781234567890",
      sources: ["YES24"],
      source_urls: ["https://yes24.com/1"],
    },
    {
      title: "같은 책",
      isbn: "9781234567890",
      sources: ["교보문고"],
      source_urls: ["https://kyobobook.co.kr/1"],
    },
  ]);
  assert.equal(merged.length, 1);
  assert.deepEqual(merged[0].sources.sort(), ["YES24", "교보문고"].sort());
  assert.equal(merged[0].source_urls.length, 2);
});

test("최종 후보는 출처별 순환 선택으로 소수 할당 출처를 보존한다", () => {
  const kpipa = SOURCES.find((item) => item.id === "kpipa");
  const hani = SOURCES.find((item) => item.id === "hani");
  const books = [
    ...Array.from({ length: 10 }, (_, index) => ({
      title: `유통 ${index}`,
      isbn: `9781234567${String(index).padStart(3, "0")}`,
      sources: [kpipa.label],
    })),
    ...Array.from({ length: 2 }, (_, index) => ({
      title: `한겨레 ${index}`,
      isbn: `9791234567${String(index).padStart(3, "0")}`,
      sources: [hani.label],
    })),
  ];
  const selected = selectFinalCandidates(books, 6);
  assert.equal(selected.filter((book) => book.sources.includes(hani.label)).length, 2);
});
