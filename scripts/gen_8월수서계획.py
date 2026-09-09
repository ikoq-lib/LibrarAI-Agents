# -*- coding: utf-8 -*-
"""
2026년 8월 도서 수서 계획 hwpx 생성 스크립트

산출물:
  1. 2026년_8월_도서수서계획_기안문.hwpx
  2. 2026년_8월_도서수서계획_세부내역.hwpx

산정 기준 (2026-07-31 사서 확정, b-01-book-acquisition.md "수서 계획 산정 기준"):
  - 정기수서 : 희망수서 = 50 : 50
  - 권당 단가 20,000원 (신간 기준)
  - 이용대상별 배분: 일반성인 50 / 청소년 10 / 어린이 25 / 유아 15
예산 근거: References/budget_2026.xlsx [4300133]도서취득비 (기준일 2026-07-07)
일정 근거: References/연간 업무 내역.xlsx — 정기도서수서 2·5·8·11월 분기 1회
"""
import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT_DIR = r"C:/Users/User/Desktop/vibe_study/LibrarAI/산출물"

OUTPUT_GIGANMUN = OUTPUT_DIR + "/2026년_8월_도서수서계획_기안문.hwpx"
OUTPUT_DETAIL = OUTPUT_DIR + "/2026년_8월_도서수서계획_세부내역.hwpx"

# ──────────────────────────────────────────────
# 공통 헬퍼 (gen_suseo_hwpx.py 검증 구조 재사용)
# ──────────────────────────────────────────────
FULL_NS = (
    'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
    'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
    'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" '
    'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
    'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" '
    'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
    'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" '
    'xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
    'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" '
    'xmlns:opf="http://www.idpf.org/2007/opf/" '
    'xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
    'xmlns:epub="http://www.idpf.org/2007/ops" '
    'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"'
)

SECPR = (
    '<hp:p id="1" paraPrIDRef="29" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
    '<hp:run charPrIDRef="0">'
    '<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" '
    'outlineShapeIDRef="1" memoShapeIDRef="1" textVerticalWidthHead="0" masterPageCnt="0">'
    '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>'
    '<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
    '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" '
    'border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>'
    '<hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>'
    '<hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY">'
    '<hp:margin header="4251" footer="4251" gutter="0" left="5669" right="5669" top="4251" bottom="4251"/>'
    '</hp:pagePr>'
    '<hp:footNotePr>'
    '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
    '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="EACH_COLUMN" beneathText="0"/>'
    '</hp:footNotePr>'
    '<hp:endNotePr>'
    '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
    '<hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="END_OF_DOCUMENT" beneathText="0"/>'
    '</hp:endNotePr>'
    '<hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '<hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '<hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '</hp:secPr>'
    '<hp:ctrl>'
    '<hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>'
    '</hp:ctrl>'
    '</hp:run>'
    '</hp:p>'
)


def para(pid, text, para_pr=7, style=0, char_pr=5):
    escaped = saxutils.escape(text)
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escaped}</hp:t></hp:run>'
        f'</hp:p>'
    )


def para_empty(pid):
    return (
        f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'
    )


def build_section0(paragraphs):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR
    ]
    for i, p in enumerate(paragraphs, start=2):
        if p is None:
            parts.append(para_empty(i))
        elif isinstance(p, str):
            parts.append(para(i, p))
        else:
            text, pp, s, cp = p
            parts.append(para(i, text, pp, s, cp))
    parts.append('</hs:sec>')
    return ''.join(parts)


def save_hwpx(section0_xml, output_path):
    with zipfile.ZipFile(TEMPLATE, 'r') as src, \
         zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            if item.filename == 'Contents/section0.xml':
                dst.writestr(item, section0_xml.encode('utf-8'))
            else:
                dst.writestr(item, src.read(item.filename))
    print(f"생성 완료: {output_path}")


def num_to_korean(n):
    units = ['', '일', '이', '삼', '사', '오', '육', '칠', '팔', '구']
    section = ['', '십', '백', '천']
    big = ['', '만', '억', '조']
    if n == 0:
        return '영'
    result = ''
    big_idx = 0
    while n > 0:
        part = n % 10000
        if part != 0:
            part_str = ''
            for i, d in enumerate(str(part).zfill(4)):
                d = int(d)
                if d == 0:
                    continue
                if d == 1 and i != 3:
                    part_str += section[3 - i]
                else:
                    part_str += units[d] + section[3 - i]
            result = part_str + big[big_idx] + result
        big_idx += 1
        n //= 10000
    return result


def won(n):
    """금000,000원(금한글원)"""
    return f"금{n:,}원(금{num_to_korean(n)}원)"


# ──────────────────────────────────────────────
# 산정 기준 및 예산 실측값
# ──────────────────────────────────────────────
# 공문서 항목기호 4수준: 1., 2. → 가., 나. → 1), 2) → 가), 나)
HANGUL_ORDER = ['가', '나', '다', '라', '마', '바', '사', '아', '자', '차']

UNIT_PRICE = 20_000                 # 권당 단가 (2026-07-31 확정)
TRACK_RATIO = 0.5                   # 정기 : 희망 = 50 : 50

# [4300133]도서취득비 — 두 라인은 용도 구분 없이 1순위부터 순차 소진 (2026-07-31 확정)
# (순위, 사업항목3, 예산액, 집행액)
BUDGET_LINES = [
    (1, "1)공공도서관자료구입(기초)|가)도서취득", 30_000_000, 17_511_570),
    (2, "2)공공도서관자료구입|가)도서취득",       28_000_000,  8_888_220),
]

BUDGET_ANNUAL = sum(b for _, _, b, _ in BUDGET_LINES)          # 58,000,000
BUDGET_SPENT = sum(s for _, _, _, s in BUDGET_LINES)           # 26,399,790
BUDGET_LEFT = BUDGET_ANNUAL - BUDGET_SPENT                     # 31,600,210

REGULAR_ROUNDS_LEFT = 2             # 정기수서 잔여 회차 (8월, 11월)
DESIRED_WEEKS_LEFT = 22             # 희망도서 잔여 주수 (2026. 8. 1. ~ 12. 31.)
AUG_WEEKS = 4                       # 8월 희망도서 처리 주기

# 이용대상별 배분 (2026-07-31 확정)
AUDIENCE = [
    ("일반성인", 50),
    ("청소년", 10),
    ("어린이", 25),
    ("유아", 15),
]

# ── 트랙별 배정 ────────────────────────────────
regular_pool = int(BUDGET_LEFT * TRACK_RATIO)          # 15,800,105
desired_pool = BUDGET_LEFT - regular_pool              # 15,800,105

# 정기수서 8월 회차: 회차 배정액을 권당 단가로 나눠 권수 확정 후 금액 역산
regular_round_cap = regular_pool // REGULAR_ROUNDS_LEFT
regular_books = regular_round_cap // UNIT_PRICE        # 395권
regular_amount = regular_books * UNIT_PRICE            # 7,900,000원

# 희망도서 8월분: 주당 배정액 → 4주분 권수 확정 후 금액 역산
desired_weekly_cap = desired_pool // DESIRED_WEEKS_LEFT
desired_books = (desired_weekly_cap * AUG_WEEKS) // UNIT_PRICE   # 143권
desired_amount = desired_books * UNIT_PRICE                      # 2,860,000원

total_books = regular_books + desired_books
total_amount = regular_amount + desired_amount

# ── 이용대상별 분야 배분 (정기수서) ─────────────
alloc = []
assigned = 0
for name, pct in AUDIENCE:
    if name == "청소년":
        continue  # 반올림 잔여분 흡수용, 마지막에 계산
    cnt = round(regular_books * pct / 100)
    alloc.append((name, pct, cnt))
    assigned += cnt
youth = regular_books - assigned
alloc.insert(1, ("청소년", 10, youth))


# ── 집행 라인 순차 소진 배정 ────────────────────
def allocate_lines(amount):
    """1순위 라인부터 잔액을 소진하며 배정. [(순위, 사업항목, 배정액, 집행전잔액, 집행후잔액)]"""
    plan = []
    remaining = amount
    for rank, name, budget, spent in BUDGET_LINES:
        avail = budget - spent
        if remaining <= 0 or avail <= 0:
            continue
        take = min(avail, remaining)
        plan.append((rank, name, take, avail, avail - take))
        remaining -= take
    if remaining > 0:
        raise ValueError(f"두 라인 합산 잔액 초과: 부족액 {remaining:,}원")
    return plan


line_plan = allocate_lines(total_amount)

print("=" * 60)
print(f"도서취득비 잔액       : {BUDGET_LEFT:,}원 (기준일 2026-07-07)")
print(f"정기 배정 / 희망 배정 : {regular_pool:,}원 / {desired_pool:,}원")
print(f"정기수서 8월 회차     : {regular_amount:,}원 / {regular_books}권")
for name, pct, cnt in alloc:
    print(f"   - {name:<5s} {pct:>2d}% : {cnt:>3d}권 / {cnt * UNIT_PRICE:>10,}원")
print(f"희망도서 8월분        : {desired_amount:,}원 / {desired_books}권 (주당 약 {desired_books / AUG_WEEKS:.0f}권)")
print(f"합계                  : {total_amount:,}원 / {total_books}권")
print("-- 집행 라인 순차 소진 --")
for rank, name, take, before, after in line_plan:
    print(f"   {rank}순위 {name}: {take:,}원 (잔액 {before:,} → {after:,})")
print("=" * 60)


# ──────────────────────────────────────────────
# 1. 기안문
# ──────────────────────────────────────────────
giganmun = [
    ("경상남도교육청 창녕도서관", 2, 0, 2),
    None,
    ("수신  내부결재", 7, 0, 5),
    ("(경유)", 7, 0, 5),
    ("제목  2026년 8월 도서 수서 계획", 7, 0, 5),
    None,
    ("1. 관련: 「2026년도 창녕도서관 장서개발계획」", 7, 0, 5),
    ("2. 2026년 8월 정기도서수서 및 희망도서수서를 다음과 같이 추진하고자 합니다.", 7, 0, 5),
    None,
    ("  가. 추진기간: 2026. 8. 1. ~ 2026. 8. 31.", 7, 0, 5),
    ("  나. 산정기준", 7, 0, 5),
    ("    1) 트랙별 예산 비중: 정기도서수서 50%, 희망도서수서 50%", 7, 0, 5),
    (f"    2) 권당 단가: {UNIT_PRICE:,}원(2024~2026년 출판 도서 실측 평균정가 18,162원 반영)", 7, 0, 5),
    ("    3) 이용대상별 배분: 일반성인 50%, 청소년 10%, 어린이 25%, 유아 15%", 7, 0, 5),
    ("  다. 예산현황(예산과목: [4300133]도서취득비, 2026. 7. 7. 기준)", 7, 0, 5),
    (f"    1) 연간 편성액: {won(BUDGET_ANNUAL)}", 7, 0, 5),
    (f"    2) 기집행액: {won(BUDGET_SPENT)}", 7, 0, 5),
    (f"    3) 잔    액: {won(BUDGET_LEFT)}", 7, 0, 5),
    ("    4) 집행순서: 두 사업항목은 용도 구분 없이 1)공공도서관자료구입(기초)을", 7, 0, 5),
    ("       우선 소진한 후 2)공공도서관자료구입을 집행", 7, 0, 5),
    ("  라. 정기도서수서(8월 회차)", 7, 0, 5),
    (f"    1) 배정액: {won(regular_amount)}", 7, 0, 5),
    (f"       (정기 배정 {regular_pool:,}원 ÷ 잔여 2회차: 8월·11월)", 7, 0, 5),
    (f"    2) 구입규모: {regular_books}권", 7, 0, 5),
    ("    3) 분야별 배분", 7, 0, 5),
] + [
    (f"      {HANGUL_ORDER[i]}) {name} {pct}%: {cnt}권({cnt * UNIT_PRICE:,}원)", 7, 0, 5)
    for i, (name, pct, cnt) in enumerate(alloc)
] + [
    ("    4) 추진절차: 수서 목록 작성 → 복본조사(B-03) → 자료심의위원회 심의 → 구입 품의", 7, 0, 5),
    ("  마. 희망도서수서(8월분)", 7, 0, 5),
    (f"    1) 배정액: {won(desired_amount)}", 7, 0, 5),
    (f"       (희망 배정 {desired_pool:,}원 ÷ 잔여 22주 × 8월 4주)", 7, 0, 5),
    (f"    2) 처리규모: {desired_books}권(주당 약 {desired_books // AUG_WEEKS}권)", 7, 0, 5),
    ("    3) 추진주기: 매주 월~일 접수, 화요일 심사 후 구입 품의", 7, 0, 5),
    (f"  바. 소요금액: {won(total_amount)}", 7, 0, 5),
    ("  사. 예산과목: [4300133]도서취득비", 7, 0, 5),
] + [
    (f"    {i + 1}) {name}: {take:,}원(집행 후 잔액 {after:,}원)", 7, 0, 5)
    for i, (rank, name, take, before, after) in enumerate(line_plan)
] + [
    None,
    ("붙임  2026년 8월 도서 수서 계획 세부내역 1부.  끝.", 7, 0, 5),
    None,
    None,
    ("                                    경상남도교육청 창녕도서관장", 7, 0, 5),
    None,
    ("기안자  기획업무팀 기획담당 주무관 서명  /  결재권자  도서관장 서명", 7, 0, 5),
    ("협조자", 7, 0, 5),
    None,
    ("시행  창녕도서관-XX(2026. 7. 31.)    접수  ( )", 7, 0, 5),
    ("우 50331 경상남도 창녕군 창녕읍 남창녕로 52 / 전화 055-530-6100 / 전송 055-530-6109 / 공개구분 공개", 7, 0, 5),
]

save_hwpx(build_section0(giganmun), OUTPUT_GIGANMUN)


# ──────────────────────────────────────────────
# 2. 붙임 — 세부내역
# ──────────────────────────────────────────────
LINE = "─" * 62

detail = [
    ("2026년 8월 도서 수서 계획 세부내역", 2, 0, 2),
    None,
    ("경상남도교육청 창녕도서관", 2, 0, 5),
    None,
    ("1. 산정 기준", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  구분                        기준값", 7, 0, 5),
    ("  트랙별 예산 비중            정기수서 50 : 희망수서 50", 7, 0, 5),
    (f"  권당 단가                   {UNIT_PRICE:,}원", 7, 0, 5),
    ("  이용대상별 배분             일반성인 50 / 청소년 10 / 어린이 25 / 유아 15 (%)", 7, 0, 5),
    (LINE, 7, 0, 5),
    None,
    ("2. 예산 현황 ([4300133]도서취득비, 기준일 2026. 7. 7.)", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  집행순위  사업항목                            편성액       집행액       잔  액", 7, 0, 5),
] + [
    (f"    {rank}순위    {name:<28s}{budget:>10,}   {spent:>10,}   {budget - spent:>10,}", 7, 0, 5)
    for rank, name, budget, spent in BUDGET_LINES
] + [
    (LINE, 7, 0, 5),
    (f"            합    계                        {BUDGET_ANNUAL:>10,}   {BUDGET_SPENT:>10,}   {BUDGET_LEFT:>10,}", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  ※ 두 사업항목은 용도 구분이 없으므로 1순위를 먼저 소진한 후 2순위를 집행함.", 7, 0, 5),
    ("  ※ 한 건의 구입이 1순위 잔액을 초과하면 1순위를 전액 소진하고 부족분만", 7, 0, 5),
    ("     2순위에서 집행하며, 결의는 사업항목별 2건으로 분할 처리함.", 7, 0, 5),
    None,
    ("3. 트랙별 배정", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  트랙            비중      배정액        산정 방식", 7, 0, 5),
    (f"  정기도서수서    50%   {regular_pool:>11,}원   잔액 × 50%, 연 4회(2·5·8·11월)", 7, 0, 5),
    (f"  희망도서수서    50%   {desired_pool:>11,}원   잔액 × 50%, 주 1회 심사", 7, 0, 5),
    (LINE, 7, 0, 5),
    None,
    ("4. 정기도서수서 8월 회차 — 이용대상별 배분", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  분야          비중       권수          금액", 7, 0, 5),
]

for name, pct, cnt in alloc:
    detail.append((f"  {name:<10s}  {pct:>3d}%   {cnt:>5d}권   {cnt * UNIT_PRICE:>11,}원", 7, 0, 5))

detail += [
    (LINE, 7, 0, 5),
    (f"  합    계      100%   {regular_books:>5d}권   {regular_amount:>11,}원", 7, 0, 5),
    (LINE, 7, 0, 5),
    (f"  ※ 배정액 산식: 정기 배정 {regular_pool:,}원 ÷ 잔여 2회차 = 회차당 {regular_round_cap:,}원", 7, 0, 5),
    (f"  ※ 권수 산식: {regular_round_cap:,}원 ÷ 권당 {UNIT_PRICE:,}원 = {regular_books}권", 7, 0, 5),
    ("  ※ 반올림 잔여분은 청소년 분야에서 조정", 7, 0, 5),
    None,
    ("5. 희망도서수서 8월분", 7, 0, 5),
    (LINE, 7, 0, 5),
    (f"  희망 배정액                {desired_pool:>11,}원", 7, 0, 5),
    ("  잔여 주수(8. 1. ~ 12. 31.)          22주", 7, 0, 5),
    (f"  주당 배정액                {desired_weekly_cap:>11,}원", 7, 0, 5),
    (f"  8월 처리 주기                        {AUG_WEEKS}주", 7, 0, 5),
    (f"  8월 배정액                 {desired_amount:>11,}원", 7, 0, 5),
    (f"  8월 처리 규모                      {desired_books}권(주당 약 {desired_books // AUG_WEEKS}권)", 7, 0, 5),
    (LINE, 7, 0, 5),
    None,
    ("6. 8월 도서취득비 집행 계획 합계", 7, 0, 5),
    (LINE, 7, 0, 5),
    (f"  정기도서수서   {regular_books:>4d}권   {regular_amount:>11,}원", 7, 0, 5),
    (f"  희망도서수서   {desired_books:>4d}권   {desired_amount:>11,}원", 7, 0, 5),
    (LINE, 7, 0, 5),
    (f"  합    계       {total_books:>4d}권   {total_amount:>11,}원", 7, 0, 5),
    (LINE, 7, 0, 5),
    None,
    ("  [집행 사업항목 배정 — 순차 소진]", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  순위  사업항목                            집행 전 잔액      배정액   집행 후 잔액", 7, 0, 5),
] + [
    (f"  {rank}순위  {name:<28s}{before:>12,}  {take:>10,}  {after:>12,}", 7, 0, 5)
    for rank, name, take, before, after in line_plan
] + [
    (LINE, 7, 0, 5),
    None,
    ("7. 권당 단가 산정 근거", 7, 0, 5),
    ("  소장 장서 73,104권의 정가 평균은 14,614원(중앙값 13,800원)이나, 이는 구간(舊刊)", 7, 0, 5),
    ("  장서가 평균을 낮춘 값으로 신간 수서 계획에 적용하기 부적합함.", 7, 0, 5),
    ("  출판연도별 실측 평균정가는 다음과 같이 상승 추세임.", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  출판연도      표본       평균정가      중앙값", 7, 0, 5),
    ("  2020년      5,092권      14,341원     14,000원", 7, 0, 5),
    ("  2022년      3,952권      16,263원     15,000원", 7, 0, 5),
    ("  2024년      3,485권      17,879원     17,000원", 7, 0, 5),
    ("  2025년      2,961권      18,231원     17,500원", 7, 0, 5),
    ("  2026년      1,265권      18,781원     17,500원", 7, 0, 5),
    (LINE, 7, 0, 5),
    ("  2024~2026년 출판분 평균 18,162원 및 상승 추세를 반영하여 권당 20,000원으로 책정함.", 7, 0, 5),
    None,
    ("8. 확인 필요 사항", 7, 0, 5),
    ("  가. 이용대상별 배분(일반성인·청소년·어린이·유아)은 이용대상 분류로, 장서 균형", 7, 0, 5),
    ("      관리에 사용하는 KDC 주제 분류와 축이 상이함. 두 기준의 매핑 규칙 확정 전", 7, 0, 5),
    ("      까지는 각각 별도 항목으로 관리함.", 7, 0, 5),
    None,
    ("끝.", 7, 0, 5),
]

save_hwpx(build_section0(detail), OUTPUT_DETAIL)

print("\n[산출물]")
print(f"  기안문    : {OUTPUT_GIGANMUN}")
print(f"  세부내역  : {OUTPUT_DETAIL}")
