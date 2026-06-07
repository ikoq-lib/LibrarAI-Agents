"""
5월 어린이 대상 행사 현황 보고서 (상급기관 제출용) hwpx 생성 스크립트
- 담당: 기획업무팀 기획담당
- 작성일: 2026-04-18
"""
import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_5월_어린이행사_상급기관제출보고.hwpx"

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

SECPR = '''<hp:p id="1" paraPrIDRef="29" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" outlineShapeIDRef="1" memoShapeIDRef="1" textVerticalWidthHead="0" masterPageCnt="0"><hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/><hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/><hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/><hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/><hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY"><hp:margin header="4251" footer="4251" gutter="0" left="5669" right="5669" top="4251" bottom="4251"/></hp:pagePr><hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr><hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr><hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill></hp:secPr><hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl></hp:run></hp:p>'''


def para(pid, text, para_pr=7, style=0, char_pr=5):
    escaped = saxutils.escape(text)
    return (f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escaped}</hp:t></hp:run></hp:p>')


def para_empty(pid):
    return (f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>')


def para_center_big(pid, text):
    # 대제목 17pt 가운데
    return para(pid, text, para_pr=2, style=0, char_pr=2)


def para_center(pid, text):
    return para(pid, text, para_pr=2, style=0, char_pr=0)


def para_subtitle(pid, text):
    # 소제목 15pt 좌측
    return para(pid, text, para_pr=3, style=0, char_pr=3)


def para_right(pid, text):
    # 우측 정렬 대체 (좌측 기본) - 공문 발신명의 등
    return para(pid, text, para_pr=2, style=0, char_pr=0)


# --------------------------------------------------------
# 공문 본문 구성
# --------------------------------------------------------
content = []
pid = 2

def add(fn, *args, **kwargs):
    global pid
    content.append(fn(pid, *args, **kwargs))
    pid += 1

def add_empty():
    global pid
    content.append(para_empty(pid))
    pid += 1


# === 문서 머리 ===
add(para_center_big, "공 공 도 서 관")
add_empty()
add(para_subtitle, "수신  : 상급기관장")
add(para_subtitle, "(경유) :")
add(para_subtitle, "제목  : 2026년 5월 어린이 대상 행사 운영 현황 제출")
add_empty()

# === 본문 인사 ===
add(para, "1. 관련: 상급기관-2026-○○○호(2026. 4. 17.) 「5월 어린이 대상 행사 운영 현황 제출 요청」")
add_empty()
add(para, "2. 위와 관련하여 우리 도서관에서 2026년 5월 중 운영 예정인 어린이 대상 행사 현황을 붙임과 같이 제출합니다.")
add_empty()
add_empty()

# === 붙임 ===
add(para_subtitle, "붙임  1. 2026년 5월 어린이 대상 행사 운영 현황  1부.  끝.")
add_empty()
add_empty()

# === 발신명의 ===
add(para_center_big, "공 공 도 서 관 장")
add_empty()
add_empty()

# === 결재란 정보 ===
add(para, "담당자      기획업무팀 기획담당")
add(para, "시행일자    2026. 4. 18.")
add(para, "접수일자")
add_empty()
add(para, "주소 : 공공도서관")
add(para, "전화 : ○○○-○○○-○○○○    /    팩스 : ○○○-○○○-○○○○")
add_empty()
add_empty()

# ======================================================
# 붙임: 현황 상세
# ======================================================
add(para_center_big, "[붙임] 2026년 5월 어린이 대상 행사 운영 현황")
add_empty()

# 1. 개요
add(para_subtitle, "1. 개    요")
add(para, "  가. 행사명 : 2026년 5월 「함께 읽는 우리 - 가족 독서의 달」 어린이 특화 프로그램")
add(para, "  나. 기  간 : 2026. 5. 1.(금) ~ 5. 31.(일)")
add(para, "  다. 장  소 : 공공도서관 어린이자료실, 제2·3강의실, 로비")
add(para, "  라. 대  상 : 관내 어린이(만 5세 ~ 초등학생) 및 가족")
add(para, "  마. 주  관 : 공공도서관 기획업무팀(기획담당)")
add_empty()

# 2. 추진 배경
add(para_subtitle, "2. 추진 배경")
add(para, "  가. 어린이날(5.5.)·어버이날(5.8.)이 있는 「가족의 달」의 의미 확산")
add(para, "  나. 어린이의 자기표현력·독서 친밀도 향상과 가족 간 독서 소통 증진")
add(para, "  다. 상급기관 「2026년 독서문화진흥 시행계획」 과제와의 연계 추진")
add_empty()

# 3. 행사 구성 (어린이 대상 5종)
add(para_subtitle, "3. 어린이 대상 행사 구성 (총 5종)")
add_empty()

# 행사 1
add(para, "  [행사 1] 어린이 북큐레이션 『엄마·아빠랑 같이 읽고 싶은 책』")
add(para, "    - 대    상 : 어린이 및 가족 (자유관람)")
add(para, "    - 일    정 : 2026. 5. 1.(금) ~ 5. 31.(일) / 상시 전시")
add(para, "    - 장    소 : 어린이자료실 큐레이션 코너")
add(para, "    - 내    용 : 부모와 함께 읽기 좋은 그림책·동화 8권 테마 전시, 짧은 해설 카드 부착")
add(para, "    - 예    산 : 없음 (기존 장서 활용)")
add_empty()

# 행사 2
add(para, "  [행사 2] 어린이날 편지 쓰기 『사랑해요, 우리 가족』")
add(para, "    - 대    상 : 어린이 (만 5세 ~ 초등학생), 자유 방문")
add(para, "    - 일    정 : 2026. 5. 5.(화·어린이날) 10:00 ~ 17:00")
add(para, "    - 장    소 : 도서관 1층 로비 특별 부스")
add(para, "    - 내    용 : 가족에게 전하는 손편지 작성, 편지지·봉투·스티커 무료 제공, 전시 후 귀가")
add(para, "    - 예    산 : 금70,000원 (편지지·봉투·스티커 등 재료비)")
add_empty()

# 행사 3
add(para, "  [행사 3] 우리 가족 이야기책 만들기")
add(para, "    - 대    상 : 어린이-보호자 동반 10가족 (사전신청)")
add(para, "    - 일    정 : 2026. 5. 9.(토) 14:00 ~ 16:00 (2시간)")
add(para, "    - 장    소 : 제2강의실 (10명 수용)")
add(para, "    - 내    용 : 가족의 추억을 그림·글로 엮어 세상에 하나뿐인 작은 책 제작")
add(para, "    - 예    산 : 금86,000원 (제본키트·채색도구 등)")
add_empty()

# 행사 4 (신규 기획 - 어린이 전용)
add(para, "  [행사 4] 어린이 독서 놀이터 『그림책 속으로』 (신규)")
add(para, "    - 대    상 : 초등 저학년(1~3학년) 15명 (사전신청)")
add(para, "    - 일    정 : 2026. 5. 16.(토) 10:30 ~ 12:00 (1시간 30분)")
add(para, "    - 장    소 : 제3강의실")
add(para, "    - 내    용 : 사서가 들려주는 그림책 낭독 + 등장인물 역할놀이·종이인형 만들기")
add(para, "    - 운    영 : 사서 직접 진행")
add(para, "    - 예    산 : 금60,000원 (미술재료·간식)")
add_empty()

# 행사 5 (신규 기획 - 어린이 전용)
add(para, "  [행사 5] 어린이 사서 체험 『하루 사서가 되어볼래?』 (신규)")
add(para, "    - 대    상 : 초등 고학년(4~6학년) 10명 (사전신청)")
add(para, "    - 일    정 : 2026. 5. 24.(일) 14:00 ~ 16:00 (2시간)")
add(para, "    - 장    소 : 어린이자료실 및 사무실")
add(para, "    - 내    용 : 도서 분류(KDC) 체험, 대출·반납 실습, 서가 정리, 체험증 수여")
add(para, "    - 운    영 : 사서 직접 진행")
add(para, "    - 예    산 : 금50,000원 (명찰·체험증·기념품)")
add_empty()

# 4. 운영 계획 요약
add(para_subtitle, "4. 운영 계획 요약")
add(para, "  가. 홍보")
add(para, "    1) 2026. 4. 20.(월) 홈페이지·SNS 사전 공지")
add(para, "    2) 2026. 4. 24.(금) 지역 일간지 보도자료 배포(기 작성 완료)")
add(para, "    3) 관내 초등학교 및 어린이집 대상 안내문 발송")
add(para, "  나. 신청")
add(para, "    1) 사전신청 3종(행사 3·4·5) : 2026. 4. 25.(토) 09:00 개시")
add(para, "    2) 신청 방법 : 홈페이지 온라인 접수 또는 도서관 방문 접수")
add(para, "  다. 안전 관리")
add(para, "    1) 어린이 보호자 동반 원칙(행사 3), 단독 참여 시 비상연락망 확보")
add(para, "    2) 현장 안전요원 1명 이상 상시 배치")
add(para, "  라. 예산 총액")
add(para, "    - 총 5종 합계 : 금266,000원 (도서관 자체예산으로 집행)")
add_empty()

# 5. 기대효과
add(para_subtitle, "5. 기대 효과")
add(para, "  가. 어린이의 독서 친밀도 및 자기표현력 향상")
add(para, "  나. 가족 단위 도서관 이용 활성화 및 세대 간 소통 증진")
add(para, "  다. 「어린이 사서 체험」 등 진로 연계 프로그램을 통한 공공도서관 인지도 제고")
add_empty()

# 6. 행정 사항
add(para_subtitle, "6. 행정 사항")
add(para, "  가. 본 계획은 수립일로부터 시행하며, 세부 운영 시 변경될 수 있음")
add(para, "  나. 결과 보고는 2026. 6. 10.(수) 이내 상급기관에 별도 제출 예정")
add_empty()
add_empty()

# ======================================================
# 요약 통계 (ASCII 차트)
# ======================================================
add(para_subtitle, "[참 고] 어린이 대상 행사 예산 배분 현황")
add_empty()
add(para, "  (단위: 원)")
add(para, "  ─────────────────────────────────────────────")
add(para, "  행사명                          예산      비율")
add(para, "  ─────────────────────────────────────────────")
add(para, "  1. 어린이 북큐레이션             0원      0.0%")
add(para, "  2. 어린이날 편지 쓰기       70,000원     26.3%  ████████")
add(para, "  3. 우리 가족 이야기책 만들기 86,000원     32.3%  ██████████")
add(para, "  4. 그림책 속으로(신규)       60,000원     22.6%  ███████")
add(para, "  5. 하루 사서 체험(신규)      50,000원     18.8%  ██████")
add(para, "  ─────────────────────────────────────────────")
add(para, "  합    계                   266,000원    100.0%")
add(para, "  ─────────────────────────────────────────────")
add_empty()

add(para, "  (단위: 명)")
add(para, "  ─────────────────────────────────────────────")
add(para, "  대상 구분        정원      비고")
add(para, "  ─────────────────────────────────────────────")
add(para, "  자유 참여(1,2)   제한없음  상시 전시 및 당일 참여")
add(para, "  사전신청(3)      10가족    가족 단위")
add(para, "  사전신청(4)      15명      초등 저학년")
add(para, "  사전신청(5)      10명      초등 고학년")
add(para, "  ─────────────────────────────────────────────")
add_empty()
add_empty()

# === 작성 정보 ===
add(para_subtitle, "※ 작성 정보")
add(para, "  - 작성일    : 2026. 4. 18.(토)")
add(para, "  - 작성부서  : 공공도서관 기획업무팀 기획담당")
add(para, "  - 제출일    : 2026. 4. 18.")
add(para, "  - 문서종류  : 상급기관 제출용 공문(보고)")
add_empty()
add(para_center, "-  끝  -")


# --------------------------------------------------------
# section0.xml 빌드 및 파일 저장
# --------------------------------------------------------
section0 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    f'<hs:sec {FULL_NS}>'
    + SECPR
    + ''.join(content)
    + '</hs:sec>'
)

with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
