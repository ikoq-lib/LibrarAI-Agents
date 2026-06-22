module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'OPENROUTER_API_KEY가 서버에 설정되지 않았습니다.' });

  try {
    const upstream = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
        'HTTP-Referer': 'https://librar-ai-agents.vercel.app',
        'X-Title': 'LibrarAI Monthly Event Planner',
      },
      body: JSON.stringify(req.body),
    });
    const text = await upstream.text();
    if (!text || !text.trim()) {
      return res.status(502).json({ error: `OpenRouter에서 빈 응답이 반환되었습니다 (HTTP ${upstream.status}). 잠시 후 다시 시도하세요.` });
    }
    let data;
    try {
      data = JSON.parse(text);
    } catch {
      return res.status(502).json({ error: `OpenRouter 응답 파싱 실패: ${text.slice(0, 200)}` });
    }
    res.status(upstream.status).json(data);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
