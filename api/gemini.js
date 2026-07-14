// B-01 수서 에이전트 전용 — Gemini API + google_search 그라운딩 도구 호출.
// 다른 모든 에이전트는 api/chat.js(OpenRouter)를 그대로 사용하고, B-01만 이 엔드포인트를 탄다.
module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'GEMINI_API_KEY가 서버에 설정되지 않았습니다.' });

  const { model, systemInstruction, contents, grounding, thinkingBudget } = req.body;
  // 기본값: 버전 고정 대신 최신 Flash 별칭 사용 — 특정 버전(예: 2.5-flash)은 신규 키에 대해 언제든
  // 서비스 종료(404)될 수 있음(2026-07-10 실제 발생). 필요 시 요청 body의 model 값으로 교체 가능.
  const modelName = model || 'gemini-flash-latest';
  // 2026-07-10: FN-01 신간 후보 수집을 네이버 책 검색 API(결정론적 호출)로 대체하면서
  // google_search 그라운딩은 기본 비활성화. 요청 body에 grounding:true를 명시할 때만 켠다
  // (턴당 검색 반복 호출로 토큰·비용 폭증, 30초 타임아웃 근접 문제가 있었음 — 되돌릴 필요 없이 옵션화).
  // thinking(내부 추론) 기본 비활성화 — 55건 점수화 같은 무거운 요청에서 thinking 토큰이 응답 시간을
  // 60초 이상으로 늘려 타임아웃을 유발함(2026-07-10 실측). 필요 시 body에 thinkingBudget 지정 가능.

  try {
    const upstream = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${modelName}:generateContent?key=${apiKey}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contents,
          ...(systemInstruction ? { systemInstruction: { parts: [{ text: systemInstruction }] } } : {}),
          ...(grounding ? { tools: [{ google_search: {} }] } : {}),
          generationConfig: { thinkingConfig: { thinkingBudget: thinkingBudget != null ? thinkingBudget : 0 } },
        }),
      }
    );
    const text = await upstream.text();
    if (!text || !text.trim()) {
      return res.status(502).json({ error: `Gemini에서 빈 응답이 반환되었습니다 (HTTP ${upstream.status}).` });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return res.status(502).json({ error: `Gemini 응답 파싱 실패: ${text.slice(0, 200)}` });
    }
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
