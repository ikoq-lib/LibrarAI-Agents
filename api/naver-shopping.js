// D-02 행사기획 에이전트 전용 — 네이버 쇼핑 검색 API 프록시.
// 브라우저에서 네이버 API를 직접 호출하면 CORS로 막히기 때문에 서버리스 함수로 중계한다.
// 행사 준비물·재료의 실제 구매처·가격·링크를 결정론적으로 조회해 LLM이 링크를 지어내지 않도록 한다.
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const clientId = process.env.NAVER_CLIENT_ID;
  const clientSecret = process.env.NAVER_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    return res.status(500).json({ error: 'NAVER_CLIENT_ID/NAVER_CLIENT_SECRET이 서버에 설정되지 않았습니다.' });
  }

  const { query, display, sort } = req.body || {};
  if (!query) return res.status(400).json({ error: 'query가 필요합니다.' });

  try {
    const url = `https://openapi.naver.com/v1/search/shop.json?query=${encodeURIComponent(query)}&display=${display || 5}&sort=${sort || 'sim'}`;
    const upstream = await fetch(url, {
      headers: {
        'X-Naver-Client-Id': clientId,
        'X-Naver-Client-Secret': clientSecret,
      },
    });
    const text = await upstream.text();
    if (!text || !text.trim()) {
      return res.status(502).json({ error: `네이버 API에서 빈 응답이 반환되었습니다 (HTTP ${upstream.status}).` });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return res.status(502).json({ error: `네이버 API 응답 파싱 실패: ${text.slice(0, 200)}` });
    }
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
