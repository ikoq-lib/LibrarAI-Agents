"""리재철 한글순 도서기호법 제5표 — 저자기호 계산.

전거: References/리재철 한글순도서 기호법제 제5표.xlsx (2026-08-26 실물 확인)

구조:  [저자명 첫 글자] + [저자명 둘째 글자의 기호] + [본표제 첫 글자]
       둘째 글자의 기호 = 자음기호(초성) + 모음기호(중성). 받침은 반영하지 않는다.

이 모듈은 LLM을 쓰지 않는다. 표가 결정론적이므로 코드가 계산하고 산출 과정을 함께 돌려준다.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 초성 19자 (유니코드 조합 순서)
CHOSUNG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
# 중성 21자 (유니코드 조합 순서)
JUNGSUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"

# 자음기호 — 제5표 A열
CONSONANT = {
    "ㄱ": "1", "ㄲ": "1",
    "ㄴ": "19",
    "ㄷ": "2", "ㄸ": "2",
    "ㄹ": "29",
    "ㅁ": "3",
    "ㅂ": "4", "ㅃ": "4",
    "ㅅ": "5", "ㅆ": "5",
    "ㅇ": "6",
    "ㅈ": "7", "ㅉ": "7",
    "ㅊ": "8",
    "ㅋ": "87",
    "ㅌ": "88",
    "ㅍ": "89",
    "ㅎ": "9",
}

# 모음기호 — 일반 열
VOWEL = {
    "ㅏ": "2",
    "ㅐ": "3", "ㅑ": "3", "ㅒ": "3",
    "ㅓ": "4", "ㅔ": "4", "ㅕ": "4", "ㅖ": "4",
    "ㅗ": "5", "ㅘ": "5", "ㅙ": "5", "ㅚ": "5", "ㅛ": "5",
    "ㅜ": "6", "ㅝ": "6", "ㅞ": "6", "ㅟ": "6", "ㅠ": "6",
    "ㅡ": "7", "ㅢ": "7",
    "ㅣ": "8",
}

# 모음기호 — 초성이 'ㅊ'인 글자 전용 열
VOWEL_CHIEUT = {
    "ㅏ": "2",
    "ㅐ": "2", "ㅑ": "2", "ㅒ": "2",
    "ㅓ": "3", "ㅔ": "3", "ㅕ": "3", "ㅖ": "3",
    "ㅗ": "4", "ㅘ": "4", "ㅙ": "4", "ㅚ": "4", "ㅛ": "4",
    "ㅜ": "5", "ㅝ": "5", "ㅞ": "5", "ㅟ": "5", "ㅠ": "5",
    "ㅡ": "5", "ㅢ": "5",
    "ㅣ": "6",
}

# 저자명에서 걷어낼 역할어 — 입고 목록의 저자란이 "정지아 지음"처럼 들어온다
ROLE_WORDS = (
    "지은이", "옮긴이", "그린이", "엮은이", "글쓴이", "감수자", "원작자",
    "지음", "옮김", "그림", "엮음", "글", "저", "역", "편저", "편", "원작",
    "공저", "공역", "감수", "사진", "만화",
)


class AuthorMarkError(ValueError):
    """저자기호를 계산할 수 없을 때 — 추정하지 않고 사서에게 넘긴다."""


@dataclass
class AuthorMark:
    mark: str                       # 최종 저자기호 (예: 요875루)
    base_name: str                  # 계산에 쓴 저자명 (예: 요코제키 다이)
    first_char: str                 # 저자명 첫 글자
    second_char: str                # 저자명 둘째 글자
    digits: str                     # 둘째 글자의 기호
    work_char: str                  # 본표제 첫 글자
    derivation: str                 # 사람이 읽는 산출 과정
    adjusted: int = 0               # 충돌 회피로 마지막 자리를 ±n 조정한 값
    notes: list[str] = field(default_factory=list)


def decompose(ch: str) -> tuple[str, str, str] | None:
    """한글 음절 한 글자를 (초성, 중성, 종성)으로 분해한다. 음절이 아니면 None."""
    code = ord(ch) - 0xAC00
    if not 0 <= code <= 11171:
        return None
    return CHOSUNG[code // 588], JUNGSUNG[(code % 588) // 28], ""


def syllable_digits(ch: str) -> str:
    """음절 한 글자의 리재철 기호(자음기호 + 모음기호)를 돌려준다."""
    parts = decompose(ch)
    if parts is None:
        raise AuthorMarkError(f"'{ch}'는 한글 음절이 아니라 기호를 계산할 수 없습니다.")
    cho, jung, _ = parts
    table = VOWEL_CHIEUT if cho == "ㅊ" else VOWEL
    return CONSONANT[cho] + table[jung]


def strip_roles(raw: str) -> str:
    """'정지아 지음', '지은이: 정지아' 같은 표기에서 이름만 남긴다."""
    name = raw.strip()
    if ":" in name:
        name = name.split(":", 1)[1]
    for sep in (";", "/", ",", "·", "、"):
        if sep in name:
            name = name.split(sep)[0]
    for word in sorted(ROLE_WORDS, key=len, reverse=True):
        name = name.replace(word, " ")
    return " ".join(name.split())


def hangul_chars(text: str) -> list[str]:
    """문자열에서 한글 음절만 순서대로 뽑는다(공백·구두점·로마자 제외)."""
    return [c for c in text if decompose(c) is not None]


def author_mark(base_name: str, title_proper: str) -> AuthorMark:
    """저자명과 본표제로 저자기호를 만든다.

    base_name 은 **저자기호 산출 기준 표기**다. 외국인 저자는 성 우선 도치형
    한글 음역(예: '셸리, 메리 W.')을 넘겨야 한다 — 로마자 이니셜은 쓰지 않는다.
    """
    name = strip_roles(base_name)
    chars = hangul_chars(name)
    if len(chars) == 0:
        raise AuthorMarkError(
            f"저자명 '{base_name}'에 한글 음절이 없습니다. 한글 음역 표기가 필요합니다."
        )
    if len(chars) == 1:
        raise AuthorMarkError(
            f"저자명 '{name}'이 한 글자라 둘째 글자가 없습니다. 사서 확인이 필요합니다."
        )

    title_chars = hangul_chars(title_proper)
    if not title_chars:
        raise AuthorMarkError(
            f"본표제 '{title_proper}'에 한글 음절이 없어 작품기호를 정할 수 없습니다."
        )

    first, second = chars[0], chars[1]
    digits = syllable_digits(second)
    work = title_chars[0]

    cho, jung, _ = decompose(second)
    table_note = " (ㅊ 전용 모음열)" if cho == "ㅊ" else ""
    derivation = (
        f"{first} + {second}({cho} {CONSONANT[cho]} + {jung} "
        f"{(VOWEL_CHIEUT if cho == 'ㅊ' else VOWEL)[jung]}{table_note}) + {work}"
    )
    return AuthorMark(
        mark=f"{first}{digits}{work}",
        base_name=name,
        first_char=first,
        second_char=second,
        digits=digits,
        work_char=work,
        derivation=derivation,
    )


def adjust(mark: AuthorMark, step: int) -> AuthorMark:
    """충돌 회피 — 숫자 마지막 자리를 ±step 조정한 새 저자기호를 만든다.

    마지막 자리가 9에서 +1 되거나 0에서 -1 되면 자연히 자릿수가 바뀌므로
    그 경우는 조정 불가로 보고 호출측이 다음 step 을 시도하게 한다.
    """
    value = int(mark.digits) + step
    new_digits = str(value)
    if len(new_digits) != len(mark.digits):
        raise AuthorMarkError(
            f"저자기호 {mark.mark}를 {step:+d} 조정하면 자릿수가 바뀝니다({mark.digits}→{new_digits})."
        )
    return AuthorMark(
        mark=f"{mark.first_char}{new_digits}{mark.work_char}",
        base_name=mark.base_name,
        first_char=mark.first_char,
        second_char=mark.second_char,
        digits=new_digits,
        work_char=mark.work_char,
        derivation=f"{mark.derivation} → 충돌 회피 {step:+d} 조정({mark.digits}→{new_digits})",
        adjusted=step,
        notes=list(mark.notes),
    )
