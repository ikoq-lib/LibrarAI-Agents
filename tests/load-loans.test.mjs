import test from "node:test";
import assert from "node:assert/strict";

import {
  ageGroupOf,
  colIndex,
  findDateGaps,
  findUnnamedColumn,
  hashMember,
  mapHeader,
  normalizeDate,
  parseCsv,
  parseSharedStrings,
  parseSheet,
  serialToDate,
  toLoanRow,
} from "../scripts/load-loans.mjs";

test("엑셀 열 이름을 0-based 인덱스로 바꾼다", () => {
  assert.equal(colIndex("A1"), 0);
  assert.equal(colIndex("J12"), 9);
  assert.equal(colIndex("AA3"), 26);
});

test("엑셀 날짜 일련번호를 날짜로 바꾼다", () => {
  assert.equal(serialToDate(45292), "2024-01-01");
  assert.equal(serialToDate(46234), "2026-07-31");
});

test("여러 형식의 대출일을 YYYY-MM-DD 로 통일한다", () => {
  assert.equal(normalizeDate("2024-01-01"), "2024-01-01");
  assert.equal(normalizeDate("2024-01-01 00:00:00"), "2024-01-01");
  assert.equal(normalizeDate("2024.1.6"), "2024-01-06");
  assert.equal(normalizeDate("2024/01/06"), "2024-01-06");
  assert.equal(normalizeDate("20240106"), "2024-01-06");
  assert.equal(normalizeDate(45292), "2024-01-01");
  assert.equal(normalizeDate(new Date(Date.UTC(2024, 0, 1))), "2024-01-01");
  assert.equal(normalizeDate(""), null);
  assert.equal(normalizeDate(null), null);
  // 등록번호처럼 날짜 범위를 벗어난 숫자는 날짜로 해석하지 않는다.
  assert.equal(normalizeDate("168380"), null);
});

test("신분 문자열에서 연령 구분을 뽑는다", () => {
  assert.equal(ageGroupOf("일반여자"), "adult");
  assert.equal(ageGroupOf("어린이남자"), "child");
  assert.equal(ageGroupOf("학생여자"), "youth");
  assert.equal(ageGroupOf("순회문고"), "other");
  assert.equal(ageGroupOf("책이음여자"), "adult");
  assert.equal(ageGroupOf(""), "other");
});

test("회원번호 해시는 같은 솔트에서 재현되고 솔트가 다르면 달라진다", () => {
  const a = hashMember("14802514001567", "salt-a");
  assert.equal(a, hashMember("14802514001567", "salt-a"));
  assert.notEqual(a, hashMember("14802514001567", "salt-b"));
  assert.notEqual(a, hashMember("14802514001568", "salt-a"));
  assert.equal(hashMember("", "salt-a"), null);
  // 원본 번호가 결과에 남지 않는다.
  assert.ok(!a.includes("14802514001567"));
});

test("헤더 순서가 바뀌어도 컬럼을 찾는다", () => {
  const map = mapHeader(["대출일", "등록번호", "회원번호", "청구기호"]);
  assert.equal(map.loanDate, 0);
  assert.equal(map.regNo, 1);
  assert.equal(map.member, 2);
  assert.equal(map.callNo, 3);
});

test("실제 대출내역 헤더를 인식한다", () => {
  const map = mapHeader([
    "대출회원번호", "이용자성명", "신분", "등록번호", "서명", "대출일", "자료실", "청구기호",
  ]);
  assert.deepEqual(map, {
    member: 0, name: 1, patronType: 2, regNo: 3,
    title: 4, loanDate: 5, room: 6, callNo: 7,
  });
});

test("변환된 행에 이용자성명이 담기지 않는다", () => {
  const header = ["대출회원번호", "이용자성명", "신분", "등록번호", "서명", "대출일", "자료실", "청구기호"];
  const map = mapHeader(header);
  const row = ["14802514001567", "윤미리", "일반여자", "EM0168380", "처음 듣는 의대 강의", "2024-01-01", "종합자료실", "510.1 안57처"];
  const loan = toLoanRow(row, map, "salt");

  assert.equal(JSON.stringify(loan).includes("윤미리"), false);
  assert.equal(loan.patron_type, "일반여자");
  assert.equal(loan.age_group, "adult");
  assert.equal(loan.reg_no, "EM0168380");
  assert.equal(loan.loan_date, "2024-01-01");
  assert.equal(loan.room, "종합자료실");
  assert.equal(loan.source_library, null);
});

test("대출일을 읽을 수 없는 행은 null 로 걸러낸다", () => {
  const map = mapHeader(["대출회원번호", "등록번호", "대출일"]);
  assert.equal(toLoanRow(["1", "EM1", ""], map, "salt"), null);
});

test("등록번호 앞뒤 공백을 제거한다", () => {
  const map = mapHeader(["대출회원번호", "등록번호", "대출일"]);
  const loan = toLoanRow(["1", "  EM0168380  ", "2024-01-01"], map, "salt");
  assert.equal(loan.reg_no, "EM0168380");
});

test("연속 결손 구간을 찾아낸다", () => {
  const dates = [
    "2025-12-12", "2025-12-13",
    // 2025-12-14 ~ 2025-12-31 결손(18일)
    "2026-01-01", "2026-01-02",
  ];
  const gaps = findDateGaps(dates, 5);
  assert.equal(gaps.length, 1);
  assert.deepEqual(gaps[0], { from: "2025-12-14", to: "2025-12-31", days: 18 });
});

test("짧은 휴관은 결손으로 보지 않는다", () => {
  assert.deepEqual(findDateGaps(["2026-01-01", "2026-01-04"], 5), []);
});

test("헤더 폭을 넘는 무명 컬럼을 찾는다", () => {
  const rows = [
    ["1", "EM1", "2025-09-02", "", "창녕도서관"],
    ["2", "EM2", "2025-09-03", "", "창녕도서관"],
    ["3", "EM3", "2024-01-01", "", ""],
  ];
  const found = findUnnamedColumn(rows, 3);
  assert.equal(found.index, 4);
  assert.equal(found.count, 2);
  assert.deepEqual(found.samples, ["창녕도서관"]);
});

test("무명 컬럼이 없으면 null 을 돌려준다", () => {
  assert.equal(findUnnamedColumn([["1", "EM1", "2024-01-01"]], 3), null);
});

test("자기닫힘 셀이 다음 셀 값을 삼키지 않는다", () => {
  // <c r="E2"/> 처럼 값이 없는 셀 뒤의 셀이 밀리면 대출일이 등록번호 자리로 들어간다.
  const shared = ["EM0168380", "종합자료실"];
  const xml = `<sheetData>
    <row r="2">
      <c r="A2" t="s"><v>0</v></c>
      <c r="B2"/>
      <c r="C2"><v>45292</v></c>
      <c r="D2" t="s"><v>1</v></c>
    </row>
  </sheetData>`;
  const [row] = parseSheet(xml, shared);
  assert.deepEqual(row, ["EM0168380", "", "45292", "종합자료실"]);
});

test("건너뛴 셀 위치를 빈 값으로 채운다", () => {
  const xml = `<sheetData><row r="1">
    <c r="A1"><v>1</v></c><c r="D1"><v>4</v></c>
  </row></sheetData>`;
  const [row] = parseSheet(xml, []);
  assert.deepEqual(row, ["1", "", "", "4"]);
});

test("inlineStr 셀과 XML 이스케이프를 읽는다", () => {
  const xml = `<sheetData><row r="1">
    <c r="A1" t="inlineStr"><is><t>도서 &amp; 자료</t></is></c>
  </row></sheetData>`;
  const [row] = parseSheet(xml, []);
  assert.deepEqual(row, ["도서 & 자료"]);
});

test("리치텍스트 sharedStrings 를 하나의 문자열로 잇는다", () => {
  const strings = parseSharedStrings(
    `<sst><si><t>단순</t></si><si><r><t>리치</t></r><r><t>텍스트</t></r></si></sst>`,
  );
  assert.deepEqual(strings, ["단순", "리치텍스트"]);
});

test("따옴표가 섞인 CSV 를 읽는다", () => {
  const rows = parseCsv('a,"b,c",d\n1,"큰따옴표 ""인용""",3\n');
  assert.deepEqual(rows, [["a", "b,c", "d"], ["1", '큰따옴표 "인용"', "3"]]);
});
