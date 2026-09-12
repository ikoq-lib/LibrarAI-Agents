"""리재철 제5표 저자기호 — 우리 관 실제 장서에서 확인된 13건으로 검증한다.

전거: .claude/agents/b-04-w-cataloging-worker.md '검증 예시' 표
      (References/whole_book_list_clean.csv 73,390행에서 역산·대조한 값)

실행:  python b04w/tests/test_leejaechul.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from leejaechul import AuthorMarkError, author_mark, syllable_digits  # noqa: E402

# (저자명, 본표제, 기대 저자기호)
CASES = [
    # 본표제 첫 글자가 한글이 아니면 — 영문은 한글 발음, 숫자는 한자음으로 읽는다
    # (2026-09-12 사서 확정: AI 알아보기 → 에 / 64 → 육 / I → 아)
    ("요코야마 히데오", "64", "요875육"),
    ("김영하", "I", "김64아"),
    ("홍길동", "AI 알아보기", "홍18에"),
    # 도치형 외국인명의 성이 한 글자면 이름 첫 글자를 둘째 글자로 쓴다
    # (2026-09-09 사서 확인: 「소원이 이루어지는 작은 호텔」 안자나 길 → 길62소)
    ("길, 안자나", "소원이 이루어지는 작은 호텔", "길62소"),
    ("셸리, 메리 W.", "프랑켄슈타인", "셸298프"),
    ("남경환", "거북선", "남14거"),
    ("이꽃님", "악당이 사는 집", "이15악"),
    ("이동조", "스티브 잡스의 창의성을 훔쳐라", "이25스"),
    ("윤소영", "박물관에서 놀자", "윤55박"),
    ("이영득", "할머니 집에서", "이64할"),
    ("이혜란", "우리 가족입니다", "이94우"),
    ("김창옥", "소통 잘하는 아이가 사랑받는다", "김82소"),   # ㅊ 전용 모음열
    ("마쓰다 모토코", "뼈뼈 수족관", "마57뼈"),
    ("야노쉬", "바나나맛 파나마", "야195바"),               # ㄴ 3자리
    ("예림당", "어린이 음악백과", "예298어"),               # ㄹ 3자리
    ("요코제키 다이", "루팡의 딸", "요875루"),              # ㅋ 3자리
    ("한태희", "봄을 찾은 할아버지", "한883봄"),            # ㅌ 3자리
    ("제프 키니", "착해도 너무 착한 롤리의 일기", "제897착"),  # ㅍ 3자리
    # 2026-09-02 배치 산출물에서 확인한 건
    ("정지아", "찌니주의보", "정78찌"),
    ("셸리, 메리 W.", "프랑켄슈타인", "셸298프"),           # 외국인 성 우선 도치형
    # 역할어가 붙어 들어오는 입고 목록 표기
    ("지은이: 정지아", "찌니주의보", "정78찌"),
    ("정지아 지음", "찌니주의보", "정78찌"),
]

# ㅊ 전용 모음열이 일반 열과 실제로 다른지 확인
CHIEUT_CASES = [("차", "82"), ("채", "82"), ("처", "83"), ("초", "84"), ("추", "85"), ("치", "86")]
NORMAL_CASES = [("가", "12"), ("개", "13"), ("거", "14"), ("고", "15"), ("구", "16"), ("그", "17"), ("기", "18")]


def main() -> int:
    failures = []

    for name, title, expected in CASES:
        try:
            got = author_mark(name, title)
        except AuthorMarkError as exc:
            failures.append(f"{name} / {title}: 예외 {exc}")
            continue
        status = "ok " if got.mark == expected else "FAIL"
        if got.mark != expected:
            failures.append(f"{name} / {title}: 기대 {expected}, 산출 {got.mark}")
        print(f"[{status}] {name:16} {title[:20]:22} -> {got.mark:8} ({got.derivation})")

    print()
    for syllable, expected in CHIEUT_CASES + NORMAL_CASES:
        got = syllable_digits(syllable)
        if got != expected:
            failures.append(f"음절 {syllable}: 기대 {expected}, 산출 {got}")
        print(f"[{'ok ' if got == expected else 'FAIL'}] 음절 {syllable} -> {got}")

    print()
    # 한 글자 저자명은 추정하지 않고 오류를 낸다
    try:
        author_mark("설", "무제")
    except AuthorMarkError:
        print("[ok ] 한 글자 저자명은 AuthorMarkError")
    else:
        failures.append("한 글자 저자명인데 예외가 발생하지 않았습니다")

    print()
    if failures:
        print(f"실패 {len(failures)}건:")
        for f in failures:
            print("  -", f)
        return 1
    print(f"전체 통과 ({len(CASES) + len(CHIEUT_CASES) + len(NORMAL_CASES) + 1}건)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
