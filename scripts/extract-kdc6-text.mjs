// KDC6 분류표 PDF에서 텍스트를 추출해 References/KDC6_for_learning.txt 로 저장한다.
//
// 왜 이 스크립트가 필요한가:
//   References/KDC6_for_learning.pdf 는 폰트에 ToUnicode 매핑이 없어 `pdftotext` 로는
//   한글이 한 글자도 나오지 않는다(숫자만 추출되고 **에러 없이 조용히 실패**한다).
//   cp949/euc-kr/johab 로 재디코딩해도 한글 단어 0개다. Read 도구의 PDF 렌더링 경로도
//   이 환경에는 pdftoppm 이 없어 쓸 수 없다. pdf.js 기반의 pdf-parse 만 정상 동작한다.
//
//   에이전트가 매번 247쪽을 재파싱하지 않도록 결과를 텍스트로 떨어뜨려 두고,
//   .claude/agents/b-04-w-cataloging-worker.md 는 그 텍스트 파일을 참조한다.
//
// 사용법: npm run extract:kdc6   (또는 node scripts/extract-kdc6-text.mjs)

import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const pdf = require('pdf-parse');

const SRC = path.resolve('References/KDC6_for_learning.pdf');
const DEST = path.resolve('References/KDC6_for_learning.txt');

const HEADER = `# KDC6_for_learning.txt — 자동 생성 파일, 직접 편집하지 말 것
#
# 생성: npm run extract:kdc6   (원본: References/KDC6_for_learning.pdf)
# 원본 PDF는 pdftotext 로 읽으면 한글이 사라진 채 숫자만 나온다(에러 없이 조용히 실패).
# 내용을 고쳐야 하면 PDF를 교체한 뒤 스크립트를 다시 돌린다.
#
# 검색 요령: 분류기호와 표목 사이에 공백이 없다. "813 소설"이 아니라 "813소설"로 찾을 것.
#   grep -n -A 15 "^813소설" References/KDC6_for_learning.txt
# 쪽 번호는 "----- [p.N] -----" 마커로 표시돼 있다(N = PDF 물리 쪽).
# 앞부분(약 28쪽)은 조기표와 요목표, 그 뒤가 본표다. **세목은 반드시 본표에서 확인할 것** —
# 요목표에는 "813 소설"까지만 있고 .4/.5/.6/.7/.8 세분이 없어, 요목표만 보면 오분류한다.
#
# 주의 1: 이 책자는 KDC 제6판의 **간략판**(2020-12-11 최종수정)으로, 표지에
#   "분류강의를 위해 간추린 것으로서 각급 도서관의 자료조직 실무용으로는 적합하지 않습니다"
#   라고 명시되어 있다. 세목 판단에는 충분하지만 최종 근거가 필요하면 정식판을 확인할 것.
# 주의 2: KDC6는 별법(도서관이 선택하는 추가 세분)을 다수 제공한다. **우리 관이 어느 별법을
#   채택했는지는 이 파일로 알 수 없고, Supabase public.books 실장서로 확인해야 한다.**
#   예) 843은 KDC6에 시대구분(.3~.6)이 있으나 우리 관은 쓰지 않는다(전부 소수점 없는 843).
`;

// pdf-parse 는 기본적으로 쪽 경계를 남기지 않는다. 분류 근거를 "몇 쪽"으로 인용할 수 있어야
// 하므로 pagerender 훅에서 PDF 물리 쪽 번호를 직접 끼워 넣는다.
// (pdf-parse 는 pagerender 를 1쪽부터 순서대로 호출한다.)
let pageNo = 0;
const pagerender = async (pageData) => {
  pageNo += 1;
  const content = await pageData.getTextContent({
    normalizeWhitespace: false,
    disableCombineTextItems: false,
  });
  let out = '';
  let lastY;
  for (const item of content.items) {
    out += (lastY === undefined || lastY === item.transform[5]) ? item.str : '\n' + item.str;
    lastY = item.transform[5];
  }
  return `\n\n----- [p.${pageNo}] -----\n\n` + out;
};

const data = await pdf(fs.readFileSync(SRC), { pagerender });

const hangul = (data.text.match(/[가-힣]/g) || []).length;
if (hangul < 50000) {
  throw new Error(`한글 추출량이 비정상적으로 적습니다(${hangul}자). pdf-parse 버전이나 PDF를 확인하세요.`);
}

// 제어문자가 하나라도 남으면 grep 이 파일 전체를 바이너리로 판정해 검색 결과가 안 나온다.
// 내용은 건드리지 않고 제어문자만 제거한다.
// 개행(0x0A)·탭(0x09)만 남기고 나머지 C0 제어문자와 DEL(0x7F)을 버린다.
const isControl = (ch) => {
  const c = ch.codePointAt(0);
  return (c < 0x20 && c !== 0x0a && c !== 0x09) || c === 0x7f;
};
const text = Array.from(data.text.replace(/\r\n?/g, '\n'))
  .filter((ch) => !isControl(ch))
  .join('');
if (Array.from(text).some(isControl)) {
  throw new Error('제어문자가 남아 있습니다 — grep 이 바이너리로 인식할 수 있습니다.');
}

const markers = (text.match(/^----- \[p\.\d+\] -----$/gm) || []).length;
if (markers !== data.numpages) {
  throw new Error(`쪽 마커 수(${markers})가 PDF 쪽수(${data.numpages})와 다릅니다.`);
}

fs.writeFileSync(DEST, HEADER + text, 'utf8');
console.log(`${DEST}\n  ${data.numpages}쪽(마커 ${markers}개), ${text.length.toLocaleString()}자, 한글 ${hangul.toLocaleString()}자`);
