import zipfile, os, xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_8월_행사기획안.hwpx"

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

SECPR = '<hp:p id="1" paraPrIDRef="29" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" outlineShapeIDRef="1" memoShapeIDRef="1" textVerticalWidthHead="0" masterPageCnt="0"><hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/><hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/><hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/><hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/><hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY"><hp:margin header="4251" footer="4251" gutter="0" left="5669" right="5669" top="4251" bottom="4251"/></hp:pagePr><hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr><hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr><hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill></hp:secPr><hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl></hp:run></hp:p>'

def p(pid, text, para_pr=7, style=0, char_pr=5):
    escaped = saxutils.escape(str(text))
    return (f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escaped}</hp:t></hp:run></hp:p>')

def p_empty(pid):
    return f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'

def p_title(pid, text):
    return p(pid, text, para_pr=2, style=0, char_pr=2)

def p_subtitle(pid, text):
    return p(pid, text, para_pr=3, style=0, char_pr=3)

def p_center(pid, text):
    return p(pid, text, para_pr=2, style=0, char_pr=0)

paragraphs_xml = []
pid = 2

lines = [
    ("title",    "2026년 8월 도서관 행사 기획안"),
    ("empty",    ""),
    ("center",   "빛을 향해 읽다 — 여름, 책, 그리고 자유"),
    ("empty",    ""),
    ("body",     "담당부서: 기획업무팀 기획담당"),
    ("body",     "작성일: 2026년 4월 14일"),
    ("empty",    ""),
    ("subtitle", "1. 추진 개요"),
    ("body",     "o 테마: 빛을 향해 읽다 — 여름, 책, 그리고 자유"),
    ("body",     "o 기간: 2026년 8월 1일(토) ~ 8월 31일(월)"),
    ("body",     "o 대상: 전 연령 (어린이, 청소년, 성인)"),
    ("body",     "o 예산: 420,000원"),
    ("body",     "o 추진 배경: 여름방학(어린이·청소년)과 광복절(8.15)이 겹치는 8월을 맞아,"),
    ("body",     "  '빛'의 이중적 의미(광복의 빛, 지식의 빛)를 주제로 역사 독서문화 행사를 기획함."),
    ("body",     "  5월(가족 독서)·6월(환경 독서)에 이어 지속적인 월간 독서 문화 확산을 도모함."),
    ("empty",    ""),
    ("subtitle", "2. 행사 구성 (6종)"),
    ("body",     ""),
    ("body",     "[북큐레이션 2종] ——————————————————————————"),
    ("empty",    ""),
    ("body",     "■ 행사 1. 어린이 북큐레이션 — 여름방학에 읽는 우리 역사 이야기"),
    ("body",     "  - 대상: 초등학생"),
    ("body",     "  - 기간: 2026년 8월 1일~31일 (상시 전시)"),
    ("body",     "  - 장소: 어린이자료실 내 기획 전시 코너"),
    ("body",     "  - 내용: 광복절과 여름방학을 연결하는 어린이 역사 그림책·동화 8권 큐레이션"),
    ("body",     "          친일·독립운동·근현대사를 어린이 눈높이에서 접근한 도서로 구성"),
    ("body",     "  - 예산: 0원 (기존 소장 도서 활용)"),
    ("empty",    ""),
    ("body",     "■ 행사 2. 성인 북큐레이션 — 해방 이후 우리가 읽어야 할 책들"),
    ("body",     "  - 대상: 성인"),
    ("body",     "  - 기간: 2026년 8월 1일~31일 (상시 전시)"),
    ("body",     "  - 장소: 종합자료실 내 기획 전시 코너"),
    ("body",     "  - 내용: 광복 81주년을 맞아 해방 전후 역사·문학·사회를 다룬 성인 교양서 8권"),
    ("body",     "  - 예산: 0원 (기존 소장 도서 활용)"),
    ("empty",    ""),
    ("body",     "[참여형 행사 4종] ——————————————————————————"),
    ("empty",    ""),
    ("body",     "■ 행사 3. 우리 역사 독후감 엽서 쓰기"),
    ("body",     "  - 대상: 초등 1~6학년"),
    ("body",     "  - 일시: 2026년 8월 8일(토) 10:30~12:00 (90분)"),
    ("body",     "  - 장소: 2호실 (정원 10명)"),
    ("body",     "  - 내용: 어린이 역사 북큐레이션 도서 중 1권을 미리 읽고 독후감을 엽서 형식으로 꾸밈"),
    ("body",     "          완성한 엽서는 도서관 로비에 전시"),
    ("body",     "  - 진행: 사서 직접 진행"),
    ("body",     "  - 예산: 60,000원 (엽서 용지, 색연필, 스티커 등 재료비)"),
    ("empty",    ""),
    ("body",     "■ 행사 4. 여름방학 나만의 독서노트 만들기"),
    ("body",     "  - 대상: 초등 3~6학년"),
    ("body",     "  - 일시: 2026년 8월 15일(토) 10:30~12:00 (90분) — 광복절 당일"),
    ("body",     "  - 장소: 2·3호실 통합 운영 (정원 20명)"),
    ("body",     "  - 내용: 여름방학 동안 사용할 나만의 독서노트를 직접 제작"),
    ("body",     "          표지 꾸미기, 독서 기록 양식 작성 등 포함 / 완성 후 도서 1권 대출 연계"),
    ("body",     "  - 진행: 사서 직접 진행"),
    ("body",     "  - 예산: 110,000원 (무선제본 노트 키트, 스탬프 세트 등 재료비)"),
    ("empty",    ""),
    ("body",     "■ 행사 5. 청소년 역사 북토크"),
    ("body",     "  - 대상: 중·고교생 (청소년)"),
    ("body",     "  - 일시: 2026년 8월 22일(토) 14:00~16:00 (2시간)"),
    ("body",     "  - 장소: 1호실 (정원 15명)"),
    ("body",     "  - 내용: 사전 지정 도서(파친코 또는 난중일기 현대어판)를 읽고 진행하는 독서 토론"),
    ("body",     "  - 진행: 외부강사 1인 초빙"),
    ("body",     "  - 예산: 130,000원 (강사비 100,000원 + 간식비 30,000원)"),
    ("empty",    ""),
    ("body",     "■ 행사 6. 성인 여름 독서 살롱"),
    ("body",     "  - 대상: 성인 (20대 이상)"),
    ("body",     "  - 일시: 2026년 8월 29일(토) 14:00~16:00 (2시간)"),
    ("body",     "  - 장소: 1호실 (정원 15명)"),
    ("body",     "  - 내용: 성인 북큐레이션 지정 도서 중 1권을 중심으로 한 독서 토론 살롱"),
    ("body",     "          광복 81주년의 역사적 의미를 현재와 연결하는 심화 토론"),
    ("body",     "  - 진행: 외부강사 1인 초빙"),
    ("body",     "  - 예산: 120,000원 (강사비 100,000원 + 간식비 20,000원)"),
    ("empty",    ""),
    ("subtitle", "3. 예산 내역"),
    ("body",     "  행사명                         강사비       재료비/기타    소계"),
    ("body",     "  ──────────────────────────────────────────────────────────"),
    ("body",     "  어린이 북큐레이션               -            -            0원"),
    ("body",     "  성인 북큐레이션                 -            -            0원"),
    ("body",     "  역사 독후감 엽서 쓰기           -            60,000원     60,000원"),
    ("body",     "  독서노트 만들기                 -            110,000원    110,000원"),
    ("body",     "  청소년 역사 북토크              100,000원    30,000원     130,000원"),
    ("body",     "  성인 여름 독서 살롱             100,000원    20,000원     120,000원"),
    ("body",     "  ──────────────────────────────────────────────────────────"),
    ("body",     "  합계                            200,000원    220,000원    420,000원"),
    ("empty",    ""),
    ("subtitle", "4. 행사 일정표"),
    ("body",     "  날짜             행사명                      대상         장소"),
    ("body",     "  ──────────────────────────────────────────────────────────"),
    ("body",     "  8월 1일~31일    어린이 북큐레이션 (상시)     초등학생     어린이자료실"),
    ("body",     "  8월 1일~31일    성인 북큐레이션 (상시)       성인         종합자료실"),
    ("body",     "  8월 8일(토)     역사 독후감 엽서 쓰기        초등 1~6학년  2호실"),
    ("body",     "  8월 15일(토)    독서노트 만들기              초등 3~6학년  2·3호실"),
    ("body",     "  8월 22일(토)    청소년 역사 북토크           청소년        1호실"),
    ("body",     "  8월 29일(토)    성인 여름 독서 살롱          성인          1호실"),
    ("empty",    ""),
    ("body",     "이 기획안은 기획업무팀 기획담당이 작성하였습니다."),
]

for kind, text in lines:
    if kind == "title":
        paragraphs_xml.append(p_title(pid, text))
    elif kind == "subtitle":
        paragraphs_xml.append(p_subtitle(pid, text))
    elif kind == "center":
        paragraphs_xml.append(p_center(pid, text))
    elif kind == "empty":
        paragraphs_xml.append(p_empty(pid))
    else:
        paragraphs_xml.append(p(pid, text))
    pid += 1

section0 = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
    f'<hs:sec {FULL_NS}>'
    + SECPR
    + ''.join(paragraphs_xml)
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
