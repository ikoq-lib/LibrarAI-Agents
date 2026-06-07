import zipfile, os, xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_8월_행사_보도자료.hwpx"

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
    ("body",     "보  도  자  료"),
    ("body",     "배포일시: 2026년 7월 중"),
    ("body",     "담  당: 기획업무팀 기획담당"),
    ("empty",    ""),
    ("title",    "한국 공공도서관, 8월 '빛을 향해 읽다' 행사 6종 운영"),
    ("empty",    ""),
    ("body",     "— 여름방학 어린이 체험부터 광복절 성인 독서 살롱까지, 전 연령 독서문화 행사 —"),
    ("empty",    ""),
    ("subtitle", "■ 행사 개요"),
    ("body",     "한국 공공도서관은 2026년 8월 한 달간 '빛을 향해 읽다 — 여름, 책, 그리고 자유'를"),
    ("body",     "테마로 한 월간 도서관 행사 6종을 운영합니다."),
    ("empty",    ""),
    ("body",     "광복절(8월 15일)과 여름방학이 겹치는 8월의 특성을 살려, 역사 독서의 의미를"),
    ("body",     "어린이·청소년·성인 모두가 함께 체감할 수 있는 다양한 프로그램을 마련하였습니다."),
    ("body",     "5월 '가족 독서의 달', 6월 '환경 독서의 달'에 이어 이번 8월 행사는 도서관의"),
    ("body",     "월간 독서문화 시리즈의 세 번째입니다."),
    ("empty",    ""),
    ("subtitle", "■ 행사 일정 및 내용"),
    ("empty",    ""),
    ("body",     "1. 어린이 북큐레이션 — 여름방학에 읽는 우리 역사 이야기"),
    ("body",     "   - 기간: 8월 1일~31일 (상시) / 장소: 어린이자료실"),
    ("body",     "   - 어린이 역사 그림책·동화 8권 테마 전시"),
    ("empty",    ""),
    ("body",     "2. 성인 북큐레이션 — 해방 이후 우리가 읽어야 할 책들"),
    ("body",     "   - 기간: 8월 1일~31일 (상시) / 장소: 종합자료실"),
    ("body",     "   - 광복 81주년 기념 해방 전후 역사·문학·사회 교양서 8권 전시"),
    ("empty",    ""),
    ("body",     "3. 우리 역사 독후감 엽서 쓰기"),
    ("body",     "   - 일시: 8월 8일(토) 10:30~12:00 / 장소: 2호실 / 대상: 초등 1~6학년 (10명)"),
    ("body",     "   - 역사 도서 독후감을 엽서로 작성하고 도서관 로비에 전시"),
    ("empty",    ""),
    ("body",     "4. 여름방학 나만의 독서노트 만들기"),
    ("body",     "   - 일시: 8월 15일(토) 10:30~12:00 — 광복절 당일"),
    ("body",     "   - 장소: 2·3호실 / 대상: 초등 3~6학년 (20명)"),
    ("body",     "   - 직접 독서노트를 제작하고, 완성 후 도서 1권 대출 연계"),
    ("empty",    ""),
    ("body",     "5. 청소년 역사 북토크"),
    ("body",     "   - 일시: 8월 22일(토) 14:00~16:00 / 장소: 1호실 / 대상: 중·고교생 (15명)"),
    ("body",     "   - 지정 도서를 중심으로 외부 진행자와 함께하는 청소년 독서 토론"),
    ("empty",    ""),
    ("body",     "6. 성인 여름 독서 살롱"),
    ("body",     "   - 일시: 8월 29일(토) 14:00~16:00 / 장소: 1호실 / 대상: 성인 (15명)"),
    ("body",     "   - 광복 81주년의 역사적 의미를 현재와 연결하는 성인 독서 토론 살롱"),
    ("empty",    ""),
    ("subtitle", "■ 참가 신청 및 문의"),
    ("body",     "o 사전 신청이 필요한 행사는 도서관 홈페이지 또는 방문 접수"),
    ("body",     "o 북큐레이션은 별도 신청 없이 자유 관람"),
    ("body",     "o 문의: 기획업무팀 기획담당 (대표번호)"),
    ("empty",    ""),
    ("body",     "                                        — 끝 —"),
    ("empty",    ""),
    ("body",     "※ 본 보도자료는 한국 공공도서관 기획업무팀 기획담당이 작성하였습니다."),
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
