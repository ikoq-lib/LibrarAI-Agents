"""고정길이 필드(LDR·001·005·007·008)와 발행국 부호.

008은 40자리, LDR은 24자리다. 자리 계산 실수가 텍스트에서는 눈에 보이지 않으므로
여기서 위치를 상수로 두고 조립한 뒤 길이를 단언한다. 텍스트로 출력할 때만 공백을
'#'로 치환한다(말미 공백이 편집기·git에 소리 없이 지워지는 사고 방지).
"""
from __future__ import annotations

from datetime import datetime

from config import CTRL_NO_WIDTH, LDR_VALUE

# 발행국 부호 — 국립중앙도서관 KORMARC 부록 '발행국 부호표'
# https://librarian.nl.go.kr/kormarc/KSX6006-0/sub/annex_1.html
# (실물 MARC 52건에서 ulk·ggk·hck 확인)
PROVINCE_CODE = {
    "서울": "ulk", "부산": "bnk", "대구": "tgk", "인천": "ick", "광주": "kjk",
    "대전": "tjk", "울산": "usk", "세종": "sjk", "경기": "ggk", "강원": "gak",
    "충북": "hbk", "충남": "hck", "전북": "jbk", "전남": "jnk",
    "경북": "gbk", "경남": "gnk", "제주": "jjk",
}

# 시·군 → 시도. 발행지는 자료에 시·군 단위로 찍히므로 한 단계 매핑이 필요하다.
CITY_PROVINCE = {
    "서울": "서울", "부산": "부산", "대구": "대구", "인천": "인천", "광주": "광주",
    "대전": "대전", "울산": "울산", "세종": "세종",
    # 경기
    "파주": "경기", "고양": "경기", "성남": "경기", "수원": "경기", "용인": "경기",
    "안양": "경기", "부천": "경기", "김포": "경기", "남양주": "경기", "화성": "경기",
    "광명": "경기", "의정부": "경기", "군포": "경기", "하남": "경기", "시흥": "경기",
    "안산": "경기", "평택": "경기", "이천": "경기", "양주": "경기", "오산": "경기",
    "의왕": "경기", "구리": "경기", "안성": "경기", "포천": "경기", "여주": "경기",
    "동두천": "경기", "과천": "경기", "양평": "경기", "가평": "경기", "연천": "경기",
    # 강원
    "춘천": "강원", "원주": "강원", "강릉": "강원", "속초": "강원", "동해": "강원",
    "삼척": "강원", "태백": "강원", "홍천": "강원", "평창": "강원",
    # 충북·충남
    "청주": "충북", "충주": "충북", "제천": "충북", "진천": "충북", "음성": "충북",
    "천안": "충남", "아산": "충남", "공주": "충남", "보령": "충남", "논산": "충남",
    "당진": "충남", "서산": "충남", "홍성": "충남", "예산": "충남", "계룡": "충남",
    # 전북·전남
    "전주": "전북", "익산": "전북", "군산": "전북", "완주": "전북", "정읍": "전북",
    "남원": "전북", "김제": "전북",
    "목포": "전남", "여수": "전남", "순천": "전남", "나주": "전남", "광양": "전남",
    "담양": "전남", "해남": "전남", "구례": "전남",
    # 경북·경남
    "포항": "경북", "경주": "경북", "구미": "경북", "안동": "경북", "김천": "경북",
    "경산": "경북", "영주": "경북", "상주": "경북", "칠곡": "경북", "문경": "경북",
    "창원": "경남", "김해": "경남", "진주": "경남", "양산": "경남", "거제": "경남",
    "통영": "경남", "밀양": "경남", "사천": "경남", "함안": "경남", "거창": "경남",
    "창녕": "경남", "하동": "경남", "남해": "경남", "산청": "경남", "합천": "경남",
    # 제주
    "제주": "제주", "서귀포": "제주",
}

UNKNOWN_PLACE = "[발행지불명]"


def country_code(place: str) -> str | None:
    """발행지 → 008/15-17 발행국 부호. 표에 없으면 None(추정하지 않는다)."""
    if not place:
        return None
    name = place.strip().strip("[]")
    if name == UNKNOWN_PLACE.strip("[]"):
        return None
    # '경기도 파주시' 같은 표기도 받아들인다
    for city, province in CITY_PROVINCE.items():
        if name.startswith(city):
            return PROVINCE_CODE[province]
    for province, code in PROVINCE_CODE.items():
        if name.startswith(province):
            return code
    return None


def leader() -> str:
    assert len(LDR_VALUE) == 24, f"LDR이 24자가 아닙니다: {len(LDR_VALUE)}"
    return LDR_VALUE


def control_001(ctrl_no: str | int) -> str:
    digits = "".join(ch for ch in str(ctrl_no) if ch.isdigit())
    if not digits:
        raise ValueError("001에 넣을 제어번호가 없습니다.")
    if len(digits) > CTRL_NO_WIDTH:
        raise ValueError(f"제어번호가 {CTRL_NO_WIDTH}자리를 넘습니다: {digits}")
    return digits.zfill(CTRL_NO_WIDTH)


def control_005(when: datetime | None = None) -> str:
    return (when or datetime.now()).strftime("%Y%m%d%H%M%S") + ".0"


def illustration_code(illustration: str) -> str:
    """008/18-21 삽화 부호. 확인된 것만 채우고 나머지는 공백."""
    codes = ""
    text = illustration or ""
    if any(k in text for k in ("삽화", "그림", "일러스트", "천연색")):
        codes += "a"
    if "초상" in text:
        codes += "c"
    if any(k in text for k in ("도표", "표", "차트")):
        codes += "d"
    if "지도" in text:
        codes += "b"
    # 표기 순서를 부호 알파벳 순으로 맞춘다(실물 'ac', 'ad', 'abc' 모두 오름차순)
    codes = "".join(sorted(set(codes)))
    return codes.ljust(4)[:4]


def build_008(
    *,
    pub_year: str,
    country: str | None,
    illustration: str = "",
    audience: str = " ",
    has_index: bool = False,
    literary_form: str = " ",
    language: str = "kor",
    entered: datetime | None = None,
) -> str:
    """008 40자리를 조립한다. 공백은 실제 공백으로 두고, 출력할 때만 '#'로 바꾼다."""
    now = entered or datetime.now()
    year = "".join(ch for ch in (pub_year or "") if ch.isdigit())[:4]
    if len(year) != 4:
        raise ValueError(f"008에 넣을 발행년이 4자리가 아닙니다: {pub_year!r}")

    out = now.strftime("%y%m%d")            # 00-05
    out += "s"                              # 06 단일 발행년
    out += year                             # 07-10
    out += " " * 4                          # 11-14
    out += (country or "   ")[:3].ljust(3)  # 15-17
    out += illustration_code(illustration)  # 18-21
    out += (audience or " ")[0]             # 22
    out += " " * 6                          # 23-28
    out += "001" if has_index else "000"    # 29-31 기본값 000, 색인 수록 시 001
    out += " "                              # 32
    out += (literary_form or " ")[0]        # 33
    out += " "                              # 34
    out += (language or "kor")[:3].ljust(3) # 35-37
    out += " " * 2                          # 38-39

    assert len(out) == 40, f"008이 40자가 아닙니다: {len(out)}자 / {out!r}"
    return out


def hashify(value: str) -> str:
    """고정길이 필드를 텍스트로 출력할 때 공백을 '#'로 치환한다."""
    return value.replace(" ", "#")


def dehashify(value: str) -> str:
    return value.replace("#", " ")
