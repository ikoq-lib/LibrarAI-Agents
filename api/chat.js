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
        'X-Title': 'LibrarAI',
      },
      // 항상 스트리밍을 요청한다 — 클라이언트가 SSE 청크를 그대로 소비하며 진행 상황을 실시간으로 보여준다.
      body: JSON.stringify({ ...req.body, stream: true }),
    });

    const contentType = upstream.headers.get('content-type') || '';

    // 스트리밍 응답이면 OpenRouter가 보내는 SSE 청크를 가공 없이 그대로 클라이언트에 전달한다.
    if (contentType.includes('text/event-stream') && upstream.body) {
      res.writeHead(upstream.status, {
        'Content-Type': 'text/event-stream; charset=utf-8',
        'Cache-Control': 'no-cache, no-transform',
        'Connection': 'keep-alive',
      });
      const reader = upstream.body.getReader();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        res.write(value);
      }
      return res.end();
    }

    // 스트리밍이 아닌 응답(주로 요청 자체가 거부된 에러) — 기존처럼 버퍼링해 JSON으로 반환한다.
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
