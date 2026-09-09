"""출판사 → 발행지(260 $a) 해결.

발행지는 우리가 쓰는 어떤 API도 주지 않는다 — SEOJI 응답 37개 필드에 없고, 자관 장서
DB `public.books`에도 열이 없으며, data.go.kr BookInformationService는 폐기됐다
(2026-09-04 확인). 그래서 출판사 단위로 웹에서 확인해 `data/publisher_places.json`에
쌓는다. 도서 단위가 아니라 출판사 단위인 이유는 같은 출판사가 배치 안에서 여러 번
나오기 때문이다(301종에 출판사 222곳 — 79회 절약).

확인되지 않으면 비워 둔다. `[발행지불명]` + needs_info 가 추정 기재보다 낫다.
"""
from __future__ import annotations

import json
import re
import threading
import urllib.request
from pathlib import Path

from config import DATA_DIR, DEFAULT_MODEL, OPENROUTER_URL, env, with_deadline

STORE = DATA_DIR / "publisher_places.json"
_lock = threading.Lock()

SYSTEM = """당신은 한국 출판사의 등록 소재지를 확인하는 조사원입니다. 웹 검색 결과에 \
실제로 나타난 주소만 근거로 삼습니다.

- `address`는 **시·도부터 시작하는 전체 주소를 그대로** 옮겨 적습니다\
("서울특별시 중구 동호로 272"). 도로명만 적지 마십시오 — 시·군이 빠지면 쓸 수 없습니다.
- `place`는 그 주소에서 뽑은 **시·군 단위 한 단어**입니다: 서울, 파주, 고양, 성남, 부산 …
- 검색 결과에 "경기도"까지만 나오고 시·군이 없으면 `place`를 빈 문자열로 두십시오.
- 같은 이름의 출판사가 여럿이면 빈 문자열을 돌려주십시오.
- **모르면 빈 문자열입니다. 서울일 가능성이 높다는 이유로 서울이라고 적지 마십시오.**

설명 없이 JSON 하나만 출력합니다: {"place": "", "address": "", "evidence": ""}"""

# 시·군이 빠진 도로명 주소만 나올 때가 있어(실측: '디자인하우스' → '동호로 272')
# 질문을 바꿔 한 번 더 묻는다.
QUERIES = (
    "출판사 '{name}'의 등록 주소는 어디입니까? 시·도부터 시작하는 전체 도로명주소로 알려 주십시오.",
    "'{name}' 출판사(도서 『{hint}』 발행처)의 사업장 소재지를 시·군 단위까지 알려 주십시오. "
    "출판사 홈페이지 하단이나 사업자정보에 적힌 주소를 확인하십시오.",
    # 소규모 출판사는 홈페이지·사업자정보가 검색에 안 걸릴 때가 많다. 마지막에는
    # 도시 이름 하나만 물어 온라인서점 출판사 정보·판권지·보도자료까지 범위를 넓힌다.
    "출판사 '{name}'이 있는 도시는 어디입니까? 온라인서점의 출판사 정보, 책 판권지, "
    "출판사 소개 기사 등 어디서든 확인되면 그 도시 이름만 알려 주십시오.",
)


def load() -> dict:
    if not STORE.exists():
        return {"_주석": [], "places": {}}
    return json.loads(STORE.read_text(encoding="utf-8"))


def save(store: dict) -> None:
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")


def normalize(place: str) -> str:
    """'경기도 파주시' · '서울특별시' → '파주' · '서울'. 시·군을 못 집으면 빈 문자열."""
    text = (place or "").strip()
    if not text:
        return ""
    match = re.search(r"([가-힣]{2,4})\s*(?:특별자치시|특별자치도|특별시|광역시|시|군)\b", text)
    if match:
        return match.group(1)
    token = text.split()[-1]
    token = re.sub(r"(특별자치시|특별자치도|특별시|광역시|시|군)$", "", token)
    return token if 2 <= len(token) <= 4 and re.fullmatch(r"[가-힣]+", token) else ""


def _ask(question: str, model: str, timeout: int) -> tuple[dict, float]:
    body = {
        "model": model,
        "plugins": [{"id": "web", "max_results": 2}],
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": question},
        ],
    }
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env('OPENROUTER_API_KEY')}",
            "HTTP-Referer": "https://librar-ai-agents.vercel.app",
            "X-Title": "LibrarAI B-04-W",
        },
    )
    def fetch() -> dict:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    payload = with_deadline(fetch, timeout + 30)
    cost = float((payload.get("usage") or {}).get("cost") or 0.0)
    text = payload["choices"][0]["message"]["content"].strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text), cost


def resolve(publisher: str, *, store: dict, model: str = DEFAULT_MODEL,
            hint: str = "", timeout: int = 240) -> tuple[str, float]:
    """출판사 소재지를 돌려준다. 표에 있으면 조회하지 않는다. (발행지, 비용)"""
    name = (publisher or "").strip()
    if not name:
        return "", 0.0
    places = store.setdefault("places", {})
    with _lock:
        if name in places:
            return places[name], 0.0

    total = 0.0
    place, data = "", {}
    for query in QUERIES:
        data, cost = _ask(query.format(name=name, hint=hint or name), model, timeout)
        total += cost
        place = normalize(data.get("place") or "") or normalize(data.get("address") or "")
        if place:
            break

    with _lock:
        places[name] = place       # 빈 문자열도 기록한다 — 다시 물어서 돈 쓰지 않도록
        store.setdefault("_근거", {})[name] = {
            "address": data.get("address", ""),
            "evidence": data.get("evidence", ""),
        }
    return place, total
