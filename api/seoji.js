// B-01/B-02 공용 — 국립중앙도서관 서지정보유통지원시스템(SEOJI) API 프록시.
// nl.go.kr 직접 신청 경로(SearchApi.do)를 사용한다. 공공데이터포털(data.go.kr) 경유 경로
// (apis.data.go.kr/1371029/BookInformationService)는 정확한 요청 파라미터가 문서로 확인되지
// 않아(PRD b01 9장 미결사항) 사용하지 않았다 — nl.go.kr 쪽은 국립중앙도서관 공식 Open API
// 안내 페이지(nl.go.kr/NL/contents/N31101030500.do)에 명세된 파라미터를 그대로 따른다.
// 브라우저에서 직접 호출하면 CORS로 막히기 때문에 서버리스 함수로 중계한다.
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const certKey = process.env.SEOJI_API_KEY_NL_DIRECT;
  if (!certKey) {
    return res.status(500).json({ error: 'SEOJI_API_KEY_NL_DIRECT가 서버에 설정되지 않았습니다.' });
  }

  const { isbn, setIsbn, title, author, publisher, startDate, endDate, pageNo, pageSize } = req.body || {};
  if (!isbn && !setIsbn && !title && !author && !publisher && !startDate) {
    return res.status(400).json({ error: 'isbn, setIsbn, title, author, publisher, startDate 중 최소 1개는 필요합니다.' });
  }

  const params = new URLSearchParams({
    cert_key: certKey,
    result_style: 'json',
    page_no: String(pageNo || 1),
    page_size: String(pageSize || 10),
  });
  if (isbn) params.set('isbn', isbn);
  if (setIsbn) params.set('set_isbn', setIsbn);
  if (title) params.set('title', title);
  if (author) params.set('author', author);
  if (publisher) params.set('publisher', publisher);
  if (startDate) params.set('start_publish_date', startDate);
  if (endDate) params.set('end_publish_date', endDate);

  try {
    const url = `https://www.nl.go.kr/seoji/SearchApi.do?${params.toString()}`;
    const upstream = await fetch(url);
    const text = await upstream.text();
    if (!text || !text.trim()) {
      return res.status(502).json({ error: `SEOJI API에서 빈 응답이 반환되었습니다 (HTTP ${upstream.status}).` });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return res.status(502).json({ error: `SEOJI API 응답 파싱 실패: ${text.slice(0, 200)}` });
    }
    // 오류 응답 형식은 국립중앙도서관 안내 문서 기준 에러코드(000/010/011/012)만 확인되어 있고
    // 성공 시 최상위 래퍼 구조는 문서화되어 있지 않다 — docs 필드 부재로만 오류를 판단하면
    // 정상 응답의 빈 검색 결과(TOTAL_COUNT=0)까지 오류로 오판할 수 있으므로 그대로 전달하고
    // 판단은 호출측(프론트엔드)에서 docs 유무로 하게 한다.
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
