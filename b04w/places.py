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
import os
import re
import threading
import urllib.parse
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
    # 토큰 단위로 앞에서부터 시·군을 찾는다. 정규식 한 방으로 잡으면 탐욕 매칭 때문에
    # "서울특별시" → "서울특별"이 되고, "전북특별자치도 전주시"에서는 도 이름("전북")이
    # 시 이름보다 먼저 잡힌다(2026-09-09 실측).
    for token in text.split():
        for suffix in ("특별자치시", "특별시", "광역시", "시", "군"):
            if token.endswith(suffix) and not token.endswith("자치도"):
                head = token[: -len(suffix)]
                if 2 <= len(head) <= 4 and re.fullmatch(r"[가-힣]+", head):
                    return head
    # 이미 "서울"·"파주"처럼 시·군 이름만 온 경우(LLM의 place 필드)는 그대로 쓴다
    if 2 <= len(text) <= 4 and re.fullmatch(r"[가-힣]+", text) and not text.endswith("도"):
        return text
    return ""


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


def naver_local(name: str, timeout: int = 15) -> tuple[str, str, str]:
    """네이버 지역검색에서 상호가 정확히 일치하고 **업종이 출판사**인 항목을 찾는다.

    LLM 웹검색은 소규모 출판사를 못 찾는다(2026-09-04 배치에서 27곳 전멸). 지역검색은
    사업장 등록 정보라 이런 곳도 잡히는데, 대신 같은 상호의 학원·카페가 섞여 나오므로
    **업종(category)까지 출판이어야** 채택한다. 그렇게 걸러 11곳을 확인했다.

    반환: (발행지, 주소, 근거) — 확인 못 하면 ("", "", "").
    """
    client = os.environ.get("NAVER_CLIENT_ID", "")
    secret = os.environ.get("NAVER_CLIENT_SECRET", "")
    if not (client and secret and name.strip()):
        return "", "", ""
    base = re.sub(r"\(.*?\)", "", name).strip()
    target = re.sub(r"[\s()]|도서출판|주식회사|\(주\)", "", base)
    hits: dict[str, tuple[str, str, str]] = {}
    for query in (base, f"도서출판 {base}"):
        url = "https://openapi.naver.com/v1/search/local.json?" + urllib.parse.urlencode(
            {"query": query, "display": 5}
        )
        request = urllib.request.Request(
            url, headers={"X-Naver-Client-Id": client, "X-Naver-Client-Secret": secret}
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                items = json.loads(response.read().decode("utf-8")).get("items", [])
        except Exception:
            continue
        for item in items:
            title = re.sub(r"<[^>]+>", "", item.get("title", ""))
            category = item.get("category", "")
            address = item.get("roadAddress") or item.get("address") or ""
            if "출판" not in category and "도서" not in category:
                continue
            if re.sub(r"[\s()]|도서출판|주식회사|\(주\)", "", title) != target:
                continue
            hits[address] = (normalize(address), address, f"네이버 지역검색 — 상호 일치, 업종 '{category}'")
    if len(hits) == 1:                      # 주소가 둘 이상이면 어느 쪽인지 알 수 없다
        return next(iter(hits.values()))
    return "", "", ""


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

    place, address, evidence = naver_local(name)   # 무료·구조화된 경로를 먼저 쓴다
    if place:
        with _lock:
            places[name] = place
            store.setdefault("_근거", {})[name] = {"address": address, "evidence": evidence}
        return place, 0.0

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
