import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import load_env
import urllib.request

load_env.load()
api_key = load_env.get("OPENROUTER_API_KEY")

payload = json.dumps({
    "model": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "안녕하세요! 한 문장으로 자기소개 해주세요."}],
    "max_tokens": 100,
}).encode("utf-8")

req = urllib.request.Request(
    "https://openrouter.ai/api/v1/chat/completions",
    data=payload,
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(req, timeout=15) as res:
        body = json.loads(res.read().decode("utf-8"))
    print("[OK] 연결 성공!")
    print(f"모델: {body['model']}")
    print(f"응답: {body['choices'][0]['message']['content']}")
    usage = body.get("usage", {})
    print(f"토큰: 입력 {usage.get('prompt_tokens','-')} / 출력 {usage.get('completion_tokens','-')}")
except urllib.error.HTTPError as e:
    print(f"[FAIL] HTTP 오류 {e.code}: {e.read().decode()}")
except Exception as e:
    print(f"[FAIL] 오류: {e}")
