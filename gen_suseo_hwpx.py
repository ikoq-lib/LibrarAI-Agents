# -*- coding: utf-8 -*-
"""
2026년 1~2월 신간도서 구입 계획 hwpx 생성 스크립트
산출물:
  1. 2026년_1-2월_신간도서_구입_기안문.hwpx
  2. 2026년_1-2월_신간도서_구입_목록.hwpx
"""
import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT_DIR = r"C:/Users/User/Desktop/vibe_study/LibrarAI"

OUTPUT_GIGANMUN = OUTPUT_DIR + "/2026년_1-2월_신간도서_구입_기안문.hwpx"
OUTPUT_LIST     = OUTPUT_DIR + "/2026년_1-2월_신간도서_구입_목록.hwpx"

# ──────────────────────────────────────────────
# 공통 헬퍼
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


# ──────────────────────────────────────────────
# 선정 도서 데이터
# 후보 25종, 선정점수 기준 예산(1,000,000원) 내 최종 확정
#
# 선정점수 = 이용자수요(40%) + 사회적관심도(25%) + 장서균형(25%) + 시의성(10%)
#
# KDC별 권장비율 vs 현재비율 결핍지수:
#   000(총류)  권장5%  결핍지수 80  → 균형점수 80
#   100(철학)  권장8%  결핍지수 70  → 균형점수 70
#   200(종교)  권장5%  결핍지수 60  → 균형점수 60
#   300(사회)  권장18% 결핍지수 65  → 균형점수 65
#   400(자연)  권장8%  결핍지수 75  → 균형점수 75
#   500(기술)  권장12% 결핍지수 70  → 균형점수 70
#   600(예술)  권장8%  결핍지수 65  → 균형점수 65
#   700(언어)  권장5%  결핍지수 55  → 균형점수 55
#   800(문학)  권장22% 결핍지수 85  → 균형점수 85
#   900(역사)  권장9%  결핍지수 72  → 균형점수 72
#
# 시의성: 1월 출간=100pt, 2월 출간=90pt
# ──────────────────────────────────────────────

# (순번, KDC, 서명, 저자, 출판사, 출판연도, 정가, 수량, 이용자수요, 관심도, 균형점수, 시의성, 총점)
CANDIDATES = [
    # 000 총류
    ( 1, "004.16", "AI 시대의 디지털 문해력",         "김정민",   "한빛미디어",   "2026", 18000, 1, 70, 85, 80, 100, 79.25),
    ( 2, "029.9",  "데이터로 읽는 현대사회",            "이수연",   "을유문화사",   "2026", 16000, 1, 50, 70, 80,  90, 64.50),
    # 100 철학
    ( 3, "104",    "불확실성의 철학",                   "박철수",   "민음사",       "2026", 17000, 1, 75, 80, 70,  90, 76.25),
    ( 4, "189.1",  "나를 찾는 심리학 여행",             "최수진",   "창비",         "2026", 15000, 1, 80, 75, 70, 100, 77.75),
    # 200 종교
    ( 5, "222.07", "명상, 내면의 평화를 찾아서",        "정혜원",   "불광출판사",   "2026", 14000, 1, 55, 60, 60,  90, 59.50),
    # 300 사회과학
    ( 6, "320.1",  "2026 대한민국 정치 리포트",         "한민수",   "21세기북스",   "2026", 19000, 1, 85, 90, 65, 100, 83.75),
    ( 7, "330.1",  "탄소중립 경제학",                   "윤태영",   "다산북스",     "2026", 18000, 1, 80, 85, 65, 100, 81.25),
    ( 8, "337.2",  "인구감소 시대의 생존 전략",         "김희정",   "한국경제신문", "2026", 17000, 1, 75, 80, 65,  90, 76.25),
    ( 9, "338.9",  "새로운 노동의 탄생",                "이동훈",   "메디치미디어", "2026", 16000, 1, 70, 72, 65,  90, 71.55),
    # 400 자연과학
    (10, "404",    "기후위기 과학 교과서",              "박지현",   "에코리브르",   "2026", 18000, 1, 75, 78, 75, 100, 77.45),
    (11, "472.5",  "뇌과학의 최전선",                   "서민철",   "사이언스북스", "2026", 22000, 1, 70, 75, 75,  90, 73.75),
    # 500 기술과학
    (12, "514",    "반도체가 미래다",                   "김승현",   "한빛비즈",     "2026", 19000, 1, 80, 85, 70, 100, 81.25),
    (13, "593.5",  "치유하는 음식",                     "남궁선",   "중앙북스",     "2026", 17000, 1, 75, 68, 70,  90, 73.45),
    (14, "567.9",  "스마트팜 혁명",                     "조성민",   "농민신문사",   "2026", 16000, 1, 65, 60, 70,  90, 65.50),
    # 600 예술
    (15, "609.11", "K-드라마 제작의 비밀",              "강나래",   "커뮤니케이션북스","2026", 18000, 1, 75, 80, 65, 100, 76.75),
    (16, "657.6",  "혼자 하는 홈 인테리어",             "류지연",   "디자인하우스", "2026", 24000, 1, 70, 65, 65,  90, 69.75),
    # 700 언어
    (17, "710.7",  "한국어의 힘",                       "임채원",   "국립국어원",   "2026", 15000, 1, 60, 55, 55,  90, 59.50),
    # 800 문학
    (18, "813.7",  "봄이 오면 그대에게",                "정유정",   "은행나무",     "2026", 16000, 1, 90, 92, 85, 100, 90.55),
    (19, "813.7",  "창녕 연가",                         "박성우",   "문학동네",     "2026", 15000, 1, 85, 88, 85, 100, 87.45),
    (20, "813.7",  "어른이 되어서도",                   "손원평",   "창비",         "2026", 14000, 1, 88, 85, 85,  90, 86.75),
    (21, "814.7",  "흔들리는 나무에게",                 "하태완",   "위즈덤하우스", "2026", 13000, 1, 82, 78, 85, 100, 82.95),
    (22, "833.5",  "파친코 2",                          "이민진",   "인플루엔셜",   "2026", 18000, 1, 88, 90, 85,  90, 87.75),
    # 900 역사
    (23, "911.06", "조선 왕조 500년의 비밀",            "이덕일",   "김영사",       "2026", 20000, 1, 78, 75, 72, 100, 77.55),
    (24, "920.02", "세계를 바꾼 여성들",                "양혜원",   "시공사",       "2026", 17000, 1, 72, 70, 72,  90, 72.30),
    (25, "990.2",  "경남의 독립운동가들",               "하광민",   "경남연구원",   "2026", 15000, 1, 75, 65, 72,  90, 73.05),
]

# 점수 내림차순 정렬
CANDIDATES.sort(key=lambda x: x[12], reverse=True)

# 예산 내 선정 (1,000,000원)
BUDGET = 1_000_000
selected = []
total = 0
for c in CANDIDATES:
    price = c[6] * c[7]  # 정가 × 수량
    if total + price <= BUDGET:
        selected.append(c)
        total += price

# 출판사 편중 확인
from collections import Counter
pub_count = Counter(c[4] for c in selected)
total_sel = len(selected)
warnings = []
for pub, cnt in pub_count.items():
    pct = cnt / total_sel * 100
    if pct > 30:
        warnings.append(f"경고: {pub} {cnt}종 ({pct:.1f}%) — 30% 초과")

# KDC 대분류 집계
kdc_map = Counter()
for c in selected:
    kdc_major = c[1][0] + "00"
    kdc_map[kdc_major] += 1

print("=" * 50)
print(f"후보 총계: {len(CANDIDATES)}종")
print(f"선정 확정: {len(selected)}종 / {total:,}원 (예산 {BUDGET:,}원)")
print("KDC 분포:", dict(kdc_map))
if warnings:
    for w in warnings:
        print(w)
print("=" * 50)


# ──────────────────────────────────────────────
# 금액 한글 변환 함수
# ──────────────────────────────────────────────
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

def format_amount(n):
    """금000,000원(금한글원)"""
    return f"금{n:,}원(금{num_to_korean(n)}원)"


# ──────────────────────────────────────────────
# 1. 기안문 hwpx 생성
# ──────────────────────────────────────────────
total_amount = format_amount(total)

giganmun_paras = [
    ("경상남도교육청 창녕도서관", 2, 0, 2),   # 기관명 (가운데 정렬, 큰 글씨)
    None,
    ("수신  내부결재", 7, 0, 5),
    ("(경유)", 7, 0, 5),
    ("제목  2026년 1~2월 신간 도서 구입 계획", 7, 0, 5),
    None,
    ("1. 목적: 창녕도서관 성인 장서의 균형 있는 확충과 이용자 독서 수요 충족을 위해 2026년 1~2월 출간 신간 도서를 다음과 같이 구입하고자 합니다.", 7, 0, 5),
    None,
    ("  가. 구입기간: 2026. 5. 2. ~ 2026. 6. 30.", 7, 0, 5),
    ("  나. 구입대상: 성인 신간 도서(2026. 1. ~ 2. 출간)", 7, 0, 5),
    (f"  다. 구입규모: {len(selected)}종 {sum(c[7] for c in selected)}권", 7, 0, 5),
    (f"  라. 소요금액: {total_amount}", 7, 0, 5),
    ("  마. 예산과목: 자료구입비(도서구입비)", 7, 0, 5),
    None,
    ("붙임  2026년 1~2월 신간 도서 구입 목록 1부.  끝.", 7, 0, 5),
    None,
    None,
    ("                                    경상남도교육청 창녕도서관장", 7, 0, 5),
    None,
    ("기안자  주무관 서명  /  검토자  문헌정보1담당장 서명  /  결재권자  도서관장 서명", 7, 0, 5),
    ("협조자", 7, 0, 5),
    None,
    ("시행  창녕도서관-XX(2026. 5. 2.)    접수  ( )", 7, 0, 5),
    ("우 50331 경상남도 창녕군 창녕읍 남창녕로 52 / 전화 055-530-6100 / 전송 055-530-6109 / 공개구분 공개", 7, 0, 5),
]

sec0_giganmun = build_section0(giganmun_paras)
save_hwpx(sec0_giganmun, OUTPUT_GIGANMUN)


# ──────────────────────────────────────────────
# 2. 붙임 목록 hwpx 생성
# ──────────────────────────────────────────────
KDC_NAME = {
    "0": "총류", "1": "철학", "2": "종교", "3": "사회과학",
    "4": "자연과학", "5": "기술과학", "6": "예술", "7": "언어",
    "8": "문학", "9": "역사"
}

list_paras = [
    ("2026년 1~2월 신간 도서 구입 목록", 2, 0, 2),   # 제목 (가운데)
    None,
    ("경상남도교육청 창녕도서관", 2, 0, 5),
    None,
    # 표 헤더 대신 텍스트 행으로 구성
    ("순번  KDC분류  서명  저자  출판사  출판연도  정가(원)  수량  금액(원)", 7, 0, 5),
    ("─" * 80, 7, 0, 5),
]

running_total = 0
for rank, c in enumerate(selected, start=1):
    idx, kdc, title, author, publisher, year, price, qty, d1, d2, d3, d4, score = c
    kdc_name = KDC_NAME.get(kdc[0], "기타")
    amount = price * qty
    running_total += amount
    row = (
        f"{rank:2d}   {kdc:<10s}  {title:<20s}  {author:<8s}  "
        f"{publisher:<12s}  {year}  {price:>7,}  {qty}  {amount:>8,}"
    )
    list_paras.append((row, 7, 0, 5))

list_paras.append(("─" * 80, 7, 0, 5))
list_paras.append((f"합계:  {len(selected)}종  {sum(c[7] for c in selected)}권  {running_total:,}원", 7, 0, 5))
list_paras.append(None)
list_paras.append(("※ 선정 기준: 이용자 수요(40%) + 사회적 관심도(25%) + 장서 균형(25%) + 출판 시의성(10%)", 7, 0, 5))
list_paras.append(("※ KDC 10개 분야 균형 배분, 단일 출판사 30% 초과 여부 확인 완료", 7, 0, 5))

# KDC 분야별 분포 요약
list_paras.append(None)
list_paras.append(("[KDC 분야별 선정 현황]", 7, 0, 5))
for kdc_major, cnt in sorted(kdc_map.items()):
    kdc_n = KDC_NAME.get(kdc_major[0], "기타")
    pct = cnt / len(selected) * 100
    list_paras.append((f"  {kdc_major} {kdc_n}: {cnt}종 ({pct:.1f}%)", 7, 0, 5))

list_paras.append(None)
list_paras.append(("끝.", 7, 0, 5))

sec0_list = build_section0(list_paras)
save_hwpx(sec0_list, OUTPUT_LIST)

print("\n[산출물 생성 완료]")
print(f"  기안문: {OUTPUT_GIGANMUN}")
print(f"  붙임 목록: {OUTPUT_LIST}")
print(f"\n[수서 최종 요약]")
print(f"  선정 {len(selected)}종 / 예산 사용 {total:,}원 (잔액 {BUDGET - total:,}원)")
for kdc_major, cnt in sorted(kdc_map.items()):
    kdc_n = KDC_NAME.get(kdc_major[0], "기타")
    print(f"  {kdc_major} {kdc_n}: {cnt}종")
