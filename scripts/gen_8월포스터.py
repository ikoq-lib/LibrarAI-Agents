import zipfile, os, xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_8월_행사_포스터.hwpx"

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
    ("body",     "[ 홈페이지·인쇄물 포스터 원고 ]"),
    ("body",     "한국 공공도서관 | 기획업무팀 기획담당"),
    ("empty",    ""),
    ("empty",    ""),
    ("title",    "빛을 향해 읽다"),
    ("center",   "여름, 책, 그리고 자유"),
    ("empty",    ""),
    ("center",   "2026년 8월 한 달간, 도서관이 특별해집니다."),
    ("empty",    ""),
    ("empty",    ""),
    ("subtitle", "이달의 행사"),
    ("empty",    ""),
    ("body",     "  북큐레이션 (상시 전시)"),
    ("body",     "  ┌─────────────────────────────────────────────────────┐"),
    ("body",     "  │ 어린이  여름방학에 읽는 우리 역사 이야기              │"),
    ("body",     "  │         어린이자료실 | 8월 1일~31일 상시              │"),
    ("body",     "  │                                                       │"),
    ("body",     "  │ 성  인  해방 이후 우리가 읽어야 할 책들               │"),
    ("body",     "  │         종합자료실 | 8월 1일~31일 상시                │"),
    ("body",     "  └─────────────────────────────────────────────────────┘"),
    ("empty",    ""),
    ("body",     "  체험·토론 행사 (사전 신청)"),
    ("body",     "  ┌─────────────────────────────────────────────────────┐"),
    ("body",     "  │ 8월  8일(토) 10:30                                    │"),
    ("body",     "  │ 우리 역사 독후감 엽서 쓰기                            │"),
    ("body",     "  │ 초등 1~6학년 | 10명 | 2호실                          │"),
    ("body",     "  │                                                       │"),
    ("body",     "  │ 8월 15일(토) 10:30  — 광복절 특별 행사 —             │"),
    ("body",     "  │ 여름방학 나만의 독서노트 만들기                       │"),
    ("body",     "  │ 초등 3~6학년 | 20명 | 2·3호실                        │"),
    ("body",     "  │                                                       │"),
    ("body",     "  │ 8월 22일(토) 14:00                                    │"),
    ("body",     "  │ 청소년 역사 북토크                                    │"),
    ("body",     "  │ 중·고교생 | 15명 | 1호실                             │"),
    ("body",     "  │                                                       │"),
    ("body",     "  │ 8월 29일(토) 14:00                                    │"),
    ("body",     "  │ 성인 여름 독서 살롱                                   │"),
    ("body",     "  │ 성인 | 15명 | 1호실                                  │"),
    ("body",     "  └─────────────────────────────────────────────────────┘"),
    ("empty",    ""),
    ("empty",    ""),
    ("center",   "참가 신청: 도서관 홈페이지 또는 방문 접수"),
    ("center",   "문의: 기획업무팀 기획담당"),
    ("empty",    ""),
    ("center",   "한국 공공도서관"),
    ("empty",    ""),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("body",     "[ 디자인 가이드 ]"),
    ("body",     "o 색상: 여름 하늘색(#87CEEB) + 광복 태극 블루(#003478) + 흰색"),
    ("body",     "o 이미지: 펼쳐진 책 위로 빛이 쏟아지는 여름 일러스트"),
    ("body",     "o 서체: 제목 — 나눔스퀘어Bold 또는 KoPub돋움체Bold"),
    ("body",     "         본문 — 나눔스퀘어Regular"),
    ("body",     "o 규격 (인쇄물): A3 세로 (297×420mm), 해상도 300dpi"),
    ("body",     "o 규격 (홈페이지 배너): 1200×628px"),
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
