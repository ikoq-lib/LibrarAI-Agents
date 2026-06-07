import zipfile, os, xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/test_output.hwpx"

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


def para(pid, text, para_pr=7, style=0, char_pr=5):
    escaped = saxutils.escape(text)
    return (f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escaped}</hp:t></hp:run></hp:p>')

def para_empty(pid):
    return f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'

def build_section0(paragraphs):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR
    ]
    for i, p in enumerate(paragraphs, start=2):
        if isinstance(p, str):
            parts.append(para(i, p))
        else:
            text, pp, s, cp = p
            parts.append(para(i, text, pp, s, cp))
    parts.append('</hs:sec>')
    return ''.join(parts)


# 테스트 내용
paragraphs = [
    # (텍스트, paraPrIDRef, styleIDRef, charPrIDRef)
    ("hwpx 생성 테스트 문서", 2, 0, 2),       # 가운데, 17pt
    ("",),  # 빈 줄 처리는 아래에서
    ("작성일: 2026년 4월 12일     작성자: 기획업무팀 기획담당", 7, 0, 5),
    ("이 문서는 한글에서 정상적으로 열리는지 확인하기 위한 테스트 파일입니다.", 7, 0, 5),
    ("템플릿 기반 생성 방식으로 만들어졌습니다.", 7, 0, 5),
    ("소제목 테스트", 3, 0, 3),               # 좌측, 15pt
    ("- 항목 1: 정상 텍스트 출력 확인", 7, 0, 5),
    ("- 항목 2: XML 이스케이프 확인 <테스트> & '작은따옴표'", 7, 0, 5),
    ("- 항목 3: 한글 인코딩 확인 — 가나다라마바사아자차카타파하", 7, 0, 5),
]

# 빈 튜플은 별도 처리
parts = [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
    f'<hs:sec {FULL_NS}>',
    SECPR
]
pid = 2
for p in paragraphs:
    if isinstance(p, tuple) and len(p) == 1 and p[0] == "":
        parts.append(para_empty(pid))
    elif isinstance(p, tuple):
        text, pp, s, cp = p
        parts.append(para(pid, text, pp, s, cp))
    else:
        parts.append(para(pid, p))
    pid += 1
parts.append('</hs:sec>')
section0 = ''.join(parts)

# 템플릿 기반으로 생성
with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")

# 검증
with zipfile.ZipFile(OUTPUT, 'r') as z:
    files = z.namelist()
    print(f"파일 목록: {files}")
    sec = z.read('Contents/section0.xml').decode('utf-8')
    print(f"section0.xml 크기: {len(sec)} bytes")
    print(f"namespace 확인 (2011): {'hwpml/2011' in sec}")
    print(f"secPr 포함 확인: {'hp:secPr' in sec}")
