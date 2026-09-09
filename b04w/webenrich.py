"""웹검색 보강 — SEOJI가 주지 않는 값을 채운다.

SEOJI는 표제·저자·발행처·면수·판형·정가는 주지만 **발행지는 아예 없고, 목차·책소개는
표본 20건 중 2건만 채워져 있었다**(2026-09-04 실측). 분류 판단과 260 $a를 위해 이 셋을
웹에서 확인한다.

Gemini google_search 그라운딩을 먼저 쓰려 했으나 키 쿼터 소진(HTTP 429)이라
OpenRouter web 플러그인으로 대체했다. 어느 쪽이든 **검색 결과에 근거가 없으면 빈 값을
돌려주게 하고, 여기서 지어낸 값을 채우지 않는다.**
"""
from __future__ import annotations

import json
import re
import urllib.request

from config import DEFAULT_MODEL, OPENROUTER_URL, env, with_deadline
from models import BookInput

SYSTEM = """당신은 한국 공공도서관 목록담당자를 돕는 서지 조사원입니다. 웹 검색 결과에 \
실제로 나타난 정보만 옮겨 적습니다. **검색 결과에 없으면 빈 문자열이나 null을 두십시오 — \
추정·창작은 목록 오류로 직결되므로 절대 하지 마십시오.**

특히 publisher_place(발행지)는 출판사의 등록 소재지를 시·군 단위 한 단어로 적습니다\
("서울", "파주", "고양", "성남"…). "경기도"처럼 도 단위만 확인되면 빈 문자열로 두십시오.

설명 없이 JSON 객체 하나만 출력합니다."""

TEMPLATE = """다음 도서를 웹에서 확인해 JSON으로 정리하십시오.

- 서명: {title}
- 저자: {author}
- 출판사: {publisher}
- 발행년: {pub_year}
- ISBN: {isbn}

{{
  "found": true,
  "summary": "책소개 2~4문장. 검색 결과에 근거한 내용만.",
  "toc": "목차 대항목을 줄바꿈으로 나열. 없으면 빈 문자열.",
  "subject_note": "이 책의 주제를 한 문장으로. 분류 판단에 쓰입니다.",
  "kdc_guess": "예상 KDC 분류번호 3자리 강목(예: 813, 325, 517). 모르면 빈 문자열.",
  "publisher_place": "출판사 소재 시/군 한 단어. 확인 못 하면 빈 문자열.",
  "publisher_place_evidence": "발행지 근거(출처 이름). 확인 못 했으면 빈 문자열.",
  "has_illustration": true,
  "illustration_note": "삽화사항 표기(천연색삽화 / 삽화 / 빈 문자열)",
  "has_index": false,
  "has_bibliography": false,
  "is_translation": false,
  "original_title": "번역서면 원표제. 아니면 빈 문자열.",
  "original_language": "번역서면 jpn/eng/fre/ger/rus/chi/spa/ita 중 하나. 아니면 빈 문자열.",
  "original_language_ko": "번역서면 일본어/영어/프랑스어… 아니면 빈 문자열.",
  "original_author_native": "번역서면 원저자 원어 표기. 아니면 빈 문자열.",
  "author_roles": "책임표시 전체를 자료 표기대로(예: 정지아 지음 / 메리 W. 셸리 지음 ; 오숙은 옮김)",
  "series_title": "총서명. 없으면 빈 문자열.",
  "series_no": "총서 권호. 없으면 빈 문자열."
}}"""


def _post(body: dict, timeout: int) -> dict:
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
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def lookup(book: BookInput, *, model: str = DEFAULT_MODEL, max_results: int = 2,
           timeout: int = 240) -> tuple[dict, float]:
    """웹검색으로 서지 보강 정보를 가져온다. (결과 dict, 비용 USD)"""
    prompt = TEMPLATE.format(
        title=book.title or "(없음)",
        author=book.author_raw or "(없음)",
        publisher=book.publisher or "(없음)",
        pub_year=book.pub_year or "(없음)",
        isbn=book.isbn or "(없음)",
    )
    payload = with_deadline(_post, timeout + 30, {
            "model": model,
            "plugins": [{"id": "web", "max_results": max_results}],
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        },
        timeout,
    )
    if "choices" not in payload:
        raise RuntimeError(f"OpenRouter 응답에 choices가 없습니다: {str(payload)[:300]}")
    cost = float((payload.get("usage") or {}).get("cost") or 0.0)
    return _extract_json(payload["choices"][0]["message"]["content"]), cost


def apply(book: BookInput, web: dict) -> list[str]:
    """웹 조사 결과를 BookInput에 반영한다. 이미 있는 값은 건드리지 않는다."""
    notes: list[str] = []

    def put(attr: str, value, label: str) -> None:
        value = str(value or "").strip()
        if not value or getattr(book, attr):
            return
        setattr(book, attr, value)
        book.sources[label] = "웹검색"

    put("toc", web.get("toc"), "목차")
    put("summary", web.get("summary"), "책소개")
    put("series_title", web.get("series_title"), "총서")
    put("series_no", web.get("series_no"), "총서권호")
    put("illustration", web.get("illustration_note"), "삽화")
    if not book.author_raw:
        put("author_raw", web.get("author_roles"), "책임표시")

    place = str(web.get("publisher_place") or "").strip()
    if place and not book.pub_place:
        # 도 단위만 온 값은 받지 않는다 — 260 $a는 시·군 단위다
        if place.endswith("도") and len(place) <= 4:
            notes.append(f"웹 발행지 '{place}'는 도 단위라 채택하지 않았습니다.")
        else:
            book.pub_place = re.sub(r"(특별시|광역시|특별자치시|특별자치도|시|군)$", "", place) or place
            book.sources["발행지"] = f"웹검색({web.get('publisher_place_evidence') or '출처 미기재'})"

    if not str(web.get("found", True)).lower().startswith(("t", "1")) and web.get("found") is False:
        notes.append("웹검색에서 이 도서를 확인하지 못했습니다.")
    return notes
