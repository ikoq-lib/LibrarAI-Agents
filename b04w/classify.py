"""KDC 분류·주제명표목 판단 — 이 프로그램에서 LLM이 맡는 유일한 부분.

LLM에게 맡기는 것: 주제 파악(KDC 분류번호), 주제명표목·키워드, 책임표시 정리,
저자기호 산출 기준 표기(외국인 성 우선 도치형), 문학형식.

LLM에게 맡기지 않는 것: 저자기호 숫자, LDR·008 자릿수, 필드 지시기호, ISBD 구두점,
청구기호 조립, 등록번호·제어번호. 전부 결정론적이므로 코드가 계산한다.

프롬프트에는 KDC6 본표 발췌와 자관 세목 분포를 함께 넣는다 — 표만 보고 판단하면
자관이 채택하지 않은 별법으로 분류해 서가 배열이 깨진다.
"""
from __future__ import annotations

import json
import re
import urllib.request

from config import DEFAULT_MODEL, KDC6_TEXT, OPENROUTER_URL, env, with_deadline
from models import BookInput, Classification

SYSTEM_PROMPT = """당신은 한국 공공도서관의 자료조직 전문가입니다. KDC 6판과 국립중앙도서관 \
주제명표목표에 정통합니다. 도서 1건의 서지정보를 받아 **주제 판단이 필요한 항목만** JSON으로 \
돌려줍니다. 저자기호 숫자·MARC 자릿수·구두점은 호출하는 프로그램이 계산하므로 관여하지 마십시오.

## 분류 원칙
- 제목·부제·목차·책소개로 주제를 파악합니다. **ISBN 부가기호의 내용분류를 KDC로 그대로 옮기지 \
마십시오** — 출판사 신고값이라 실제 내용과 자주 어긋납니다.
- 가장 세부적인(세목, 최소 3자리) 분류번호를 부여하되, 프롬프트에 주어진 **자관 세목 분포를 \
반드시 교차검증**합니다. 표에 있는 별법이라도 자관이 쓰지 않으면 쓰지 않습니다.
- 한국문학(810)의 형식구분: 시 811 / 희곡 812 / 소설 813 / 수필 814 / 일기·서간·기행 816.
- 전기는 피전기자의 주제 분야로 분류합니다(총전기만 990).
- 목차·책소개가 없어 분류가 추정이 될 상황이면 **추정하지 말고** confidence를 "low"로 두고 \
needs_info에 무엇이 필요한지 적습니다.

## 주제명표목(650)
- 국립중앙도서관 주제명표목표 기준. 한글 표목은 **낱말 사이를 띄어 씁니다**(한국 현대 소설, 창작 그림책).
- 한자를 대응시켜 대괄호에 넣되 **한자가 없는 음절은 --로 채웁니다**(프랑스 소설[--小說], 창작 그림책[創作--冊]).
- 한자 표기가 아예 없는 표목은 대괄호를 생략합니다(글모음).
- 지역이 주제면 tag를 "651"로 합니다.
- **KSH 번호는 절대 쓰지 마십시오.** 프로그램이 사서 제공분만 채웁니다.

## 저자기호 산출 기준 표기(author_mark_base)
- 저작의 주 책임자 이름을 **한글로** 적습니다. 로마자 이니셜을 쓰지 않습니다.
- 외국인 저자는 **성 우선 도치형**으로 적습니다: "메리 W. 셸리" → "셸리, 메리 W." / \
"제프 키니" → "키니, 제프". 성이 앞에 오는 동아시아권 음역은 그대로 둡니다("요코제키 다이").
- 한국인 저자는 표기 그대로 적습니다("정지아").

## 응답 형식
설명 없이 JSON 객체 하나만 출력합니다. 모르는 값은 null 또는 빈 배열로 두고 지어내지 않습니다.

{
  "kdc": "813.7",
  "kdc_path": "8 문학 → 81 한국문학 → 813 소설 → 813.7 21세기",
  "kdc_rationale": "분류 근거 2~3문장",
  "kdc_alternatives": ["813.6"],
  "confidence": "high" | "low",
  "title_proper": "본표제(부제 제외)",
  "subtitle": "부표제 또는 null",
  "sor": ["정지아 지음", "홍길동 옮김"],
  "contributors": [
    {"name": "정지아", "dates": "1965-", "type": "person", "role": "aut", "main": true},
    {"name": "홍길동", "dates": null, "type": "person", "role": "trl", "main": false}
  ],
  "author_mark_base": "정지아",
  "author_mark_note": "한국인 저자, 표기 그대로",
  "is_translation": false,
  "original_language": null,
  "original_language_ko": null,
  "original_title": null,
  "original_author_native": null,
  "literary_form": "f",
  "subject_headings": [{"tag": "650", "term": "한국 현대 소설[韓國現代小說]"}],
  "keywords": ["귀촌"],
  "summary": "520에 넣을 2~4문장 요약. 자료 정보로 확인되는 범위에서만.",
  "has_index": false,
  "has_bibliography": false,
  "needs_info": [],
  "notes": []
}

literary_form 은 008/33 값입니다: 소설 "f" / 시 "p" / 수필·기타 문학 "m" / 비문학 " ".
contributors 의 role: 주 저자 "aut", 역자 "trl", 삽화가 "ill", 편자 "edt", 감수 "oth".
type 은 개인명 "person", 단체명 "corporate".
"""


def kdc_excerpt(hints: list[str], max_lines: int = 90) -> str:
    """KDC6 본표에서 후보 강목 주변을 발췌한다.

    PDF는 절대 파싱하지 않는다 — 이미 추출해 둔 텍스트만 쓴다(그 파일 헤더의 경고가
    별법·간략판 한계를 담고 있다).
    """
    if not KDC6_TEXT.exists():
        return "(KDC6_for_learning.txt 없음 — npm run extract:kdc6 으로 생성 필요)"
    lines = KDC6_TEXT.read_text(encoding="utf-8").splitlines()
    picked: list[str] = []
    seen: set[int] = set()
    for hint in hints:
        head = re.sub(r"[^\d]", "", hint)[:3]
        if not head:
            continue
        pattern = re.compile(rf"^{head}\D")
        for pos, line in enumerate(lines):
            if pattern.match(line):
                for offset in range(0, 18):
                    if pos + offset < len(lines) and pos + offset not in seen:
                        seen.add(pos + offset)
                        picked.append(lines[pos + offset])
                break
    return "\n".join(picked[:max_lines]) if picked else "(해당 강목을 본표에서 찾지 못함)"


def _guess_class_hints(book: BookInput) -> list[str]:
    """LLM 호출 전에 발췌할 강목 후보를 고른다(부가기호 내용분류 + 사서 힌트)."""
    hints: list[str] = []
    if book.kdc_hint:
        hints.append(book.kdc_hint)
    if len(book.isbn_add_code) == 5:
        hints.append(book.isbn_add_code[2:5])   # 셋째~다섯째 자리 = 내용분류
    return [h for h in hints if h][:3]


def build_user_prompt(book: BookInput, practice: str = "", precedents: str = "") -> str:
    lines = [
        "## 서지정보",
        f"- 본표제: {book.title}",
        f"- 부표제: {book.subtitle or '(없음)'}",
        f"- 책임표시(원문): {book.author_raw or '(없음)'}",
        f"- 출판사: {book.publisher or '(없음)'}",
        f"- 발행년: {book.pub_year or '(없음)'}",
        f"- ISBN: {book.isbn or '(없음)'} / 부가기호: {book.isbn_add_code or '(없음)'}",
        f"- 총서: {book.series_title or '(없음)'} {book.series_no}",
        f"- 대상 자료실: {book.room}",
        f"- 면수: {book.pages or '(없음)'} / 크기: {book.size_cm or '(없음)'} cm",
        f"- 목차: {(book.toc or '(없음)')[:1500]}",
        f"- 책소개: {(book.summary or '(없음)')[:1500]}",
    ]
    if book.kdc_hint:
        lines.append(f"- 사서가 제시한 분류 힌트: {book.kdc_hint} (참고만 하고 근거로 검증할 것)")

    excerpt = kdc_excerpt(_guess_class_hints(book))
    lines += ["", "## KDC6 본표 발췌 (간략판)", "```", excerpt, "```"]

    if precedents:
        lines += [
            "",
            "## 자관에 있는 같은 저자의 책 (public.books 실측)",
            "이 저자의 앞 책을 우리 관이 어디에 두었는지가 표보다 강한 근거입니다. "
            "주제가 이어지면 같은 강목을 따르고, 이번 책의 주제가 분명히 다르면 그 이유를 notes에 적으십시오.",
            "```",
            precedents,
            "```",
        ]

    if practice:
        lines += [
            "",
            "## 자관 세목 분포 (public.books 실측)",
            "표에 있는 세목이라도 자관이 쓰지 않으면 쓰지 않습니다. 압도적 다수가 쓰는 세목을 따르십시오.",
            "```",
            practice,
            "```",
        ]
    lines += ["", "위 정보로 JSON 객체 하나만 출력하십시오."]
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if fence:
        text = fence.group(1)
    else:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


def call_llm(system: str, user: str, model: str, timeout: int = 180) -> str:
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.1,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {env('OPENROUTER_API_KEY')}",
            "HTTP-Referer": "https://librar-ai-agents.vercel.app",
            "X-Title": "LibrarAI B-04-W",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "choices" not in payload:
        raise RuntimeError(f"OpenRouter 응답에 choices가 없습니다: {str(payload)[:300]}")
    return payload["choices"][0]["message"]["content"]


def classify(book: BookInput, *, model: str = DEFAULT_MODEL, practice: str = "",
             precedents: str = "") -> Classification:
    raw = with_deadline(
        call_llm, 200,
        SYSTEM_PROMPT, build_user_prompt(book, practice, precedents), model,
    )
    data = _extract_json(raw)

    result = Classification(
        kdc=str(data.get("kdc") or "").strip(),
        kdc_path=str(data.get("kdc_path") or "").strip(),
        kdc_rationale=str(data.get("kdc_rationale") or "").strip(),
        kdc_alternatives=[str(x) for x in (data.get("kdc_alternatives") or [])],
        confidence=str(data.get("confidence") or "low").lower(),
        title_proper=str(data.get("title_proper") or book.title).strip(),
        subtitle=str(data.get("subtitle") or book.subtitle or "").strip(),
        sor=[str(x).strip() for x in (data.get("sor") or []) if str(x).strip()],
        contributors=[c for c in (data.get("contributors") or []) if c.get("name")],
        author_mark_base=str(data.get("author_mark_base") or "").strip(),
        author_mark_note=str(data.get("author_mark_note") or "").strip(),
        is_translation=bool(data.get("is_translation")),
        original_language=str(data.get("original_language") or "").strip(),
        original_language_ko=str(data.get("original_language_ko") or "").strip(),
        original_title=str(data.get("original_title") or "").strip(),
        original_author_native=str(data.get("original_author_native") or "").strip(),
        literary_form=(str(data.get("literary_form") or " ") or " ")[0],
        subject_headings=[
            {"tag": str(h.get("tag") or "650"), "term": str(h.get("term") or "").strip()}
            for h in (data.get("subject_headings") or [])
            if str(h.get("term") or "").strip()
        ],
        keywords=[str(k).strip() for k in (data.get("keywords") or []) if str(k).strip()],
        summary=str(data.get("summary") or "").strip(),
        has_index=bool(data.get("has_index")),
        has_bibliography=bool(data.get("has_bibliography")),
        needs_info=[str(x) for x in (data.get("needs_info") or [])],
        notes=[str(x) for x in (data.get("notes") or [])],
    )
    # 모델이 KSH 번호를 끼워 넣어도 여기서 전부 걷어낸다 — 지어낸 번호를 실을 수 없다.
    for heading in result.subject_headings:
        heading["term"] = re.sub(r"\s*\$0\S+", "", heading["term"]).strip()
        heading.pop("ksh", None)
    return result


def offline(book: BookInput) -> Classification:
    """--no-llm 모드 — 사서가 입력한 분류를 그대로 쓰고 판단은 하지 않는다."""
    result = Classification(
        kdc=re.sub(r"[^\d.]", "", book.kdc_hint.split()[0]) if book.kdc_hint else "",
        kdc_path="(--no-llm: 입력값 사용)",
        kdc_rationale="LLM 분류를 건너뛰고 입고 목록의 분류값을 그대로 사용했습니다.",
        confidence="low",
        title_proper=book.title,
        subtitle=book.subtitle,
        sor=[book.author_raw] if book.author_raw else [],
        author_mark_base=book.author_raw,
        summary=book.summary,
    )
    if not result.kdc:
        result.needs_info.append("--no-llm 모드인데 입고 목록에 분류(KDC) 열이 없습니다.")
    return result
