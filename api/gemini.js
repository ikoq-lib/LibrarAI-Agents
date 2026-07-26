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

  const { model, systemInstruction, contents, grounding, thinkingBudget, temperature } = req.body;
  // 기본값: 버전 고정 대신 최신 Flash 별칭 사용 — 특정 버전(예: 2.5-flash)은 신규 키에 대해 언제든
  // 서비스 종료(404)될 수 있음(2026-07-10 실제 발생). 필요 시 요청 body의 model 값으로 교체 가능.
  const modelName = model || 'gemini-flash-latest';
  // 2026-07-10: FN-01 신간 후보 수집을 네이버 책 검색 API(결정론적 호출)로 대체하면서
  // google_search 그라운딩은 기본 비활성화. 요청 body에 grounding:true를 명시할 때만 켠다
  // (턴당 검색 반복 호출로 토큰·비용 폭증, 30초 타임아웃 근접 문제가 있었음 — 되돌릴 필요 없이 옵션화).
  // thinking(내부 추론): 예전엔 무거운 점수화의 타임아웃을 막으려 0(비활성화)을 기본값으로 썼으나,
  // 2026-07-26 현재 gemini-flash-latest 별칭이 gemini-3.6-flash로 이동했고 이 모델은 thinkingBudget:0을
  // 거부한다("Request contains an invalid argument." / INVALID_ARGUMENT — 실측 확인). Gemini 3.x는
  // thinking이 필수라 0으로 끌 수 없으므로, 0/미지정은 -1(동적: 모델이 예산 자동 결정)로 보정한다.
  // 지연이 문제면 body의 thinkingBudget에 양의 상한값(예: 512)을 지정해 묶을 수 있다.
  // temperature 기본 0 — B-01이 첨부된 실제 네이버/SEOJI 수집 데이터를 벗어나 존재하지 않는 도서를
  // 지어내는 사례가 있어(2026-07-16 확인) 그라운딩 정확도를 우선한다. 필요 시 body의 temperature로 override.
  const temp = temperature != null ? temperature : 0;
  const rawBudget = thinkingBudget != null ? thinkingBudget : -1;
  const budget = rawBudget === 0 ? -1 : rawBudget; // 0(비활성화)은 현재 모델에서 무효 → 동적으로 보정

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
          generationConfig: { temperature: temp, thinkingConfig: { thinkingBudget: budget } },
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
