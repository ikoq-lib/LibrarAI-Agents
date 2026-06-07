import zipfile, os, xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_8월_행사_SNS콘텐츠.hwpx"

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
    ("body",     "[ 인스타그램 SNS 콘텐츠 원고 ]"),
    ("body",     "한국 공공도서관 | 기획업무팀 기획담당"),
    ("body",     "게시 일정: 2026년 7월 말 ~ 8월 중 순차 게시"),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("empty",    ""),
    ("subtitle", "[ 카드 1 ] 메인 공지 (7월 마지막 주 게시)"),
    ("empty",    ""),
    ("body",     "  [이미지 방향]"),
    ("body",     "  여름 하늘 배경 + 펼쳐진 책 + 'AUGUST' 타이포그래피"),
    ("body",     "  색상: 하늘색 + 네이비 + 화이트"),
    ("empty",    ""),
    ("body",     "  [캡션 문구]"),
    ("body",     "  빛을 향해 읽다"),
    ("body",     "  여름, 책, 그리고 자유"),
    ("empty",    ""),
    ("body",     "  8월 한 달, 도서관이 역사와 여름을 잇습니다."),
    ("body",     "  어린이부터 성인까지 전 연령이 함께하는"),
    ("body",     "  독서문화 행사 6종이 찾아옵니다."),
    ("empty",    ""),
    ("body",     "  자세한 내용은 프로필 링크에서 확인하세요."),
    ("empty",    ""),
    ("body",     "  #도서관 #공공도서관 #8월행사 #빛을향해읽다"),
    ("body",     "  #여름방학 #광복절 #독서 #북큐레이션 #독서살롱"),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("empty",    ""),
    ("subtitle", "[ 카드 2 ] 어린이 행사 홍보 (8월 1주차 게시)"),
    ("empty",    ""),
    ("body",     "  [이미지 방향]"),
    ("body",     "  어린이가 역사책을 읽고 엽서를 쓰는 따뜻한 일러스트"),
    ("body",     "  밝은 노란색 + 파란색 조합"),
    ("empty",    ""),
    ("body",     "  [캡션 문구]"),
    ("body",     "  방학에 도서관 오세요!"),
    ("empty",    ""),
    ("body",     "  우리 역사 독후감 엽서 쓰기"),
    ("body",     "  8월 8일(토) 오전 10시 30분"),
    ("body",     "  초등 1~6학년 선착순 10명"),
    ("empty",    ""),
    ("body",     "  내가 읽은 역사책 이야기를 예쁜 엽서에 담아 보세요."),
    ("body",     "  완성된 엽서는 도서관 로비에 전시됩니다!"),
    ("empty",    ""),
    ("body",     "  신청: 홈페이지 또는 방문 접수"),
    ("empty",    ""),
    ("body",     "  #역사독후감 #엽서만들기 #어린이도서관 #여름방학체험"),
    ("body",     "  #초등학생 #도서관행사"),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("empty",    ""),
    ("subtitle", "[ 카드 3 ] 광복절 특별 행사 홍보 (8월 10~12일 게시)"),
    ("empty",    ""),
    ("body",     "  [이미지 방향]"),
    ("body",     "  태극기 색상(빨강·파랑) 포인트 + 독서노트 일러스트"),
    ("body",     "  '8.15 광복절 특별 행사' 배지 삽입"),
    ("empty",    ""),
    ("body",     "  [캡션 문구]"),
    ("body",     "  광복절엔 도서관에서 나만의 독서노트를 만들어요!"),
    ("empty",    ""),
    ("body",     "  여름방학 나만의 독서노트 만들기"),
    ("body",     "  8월 15일(토) 오전 10시 30분  — 광복절 당일"),
    ("body",     "  초등 3~6학년 선착순 20명 | 2·3호실"),
    ("empty",    ""),
    ("body",     "  직접 꾸민 나만의 독서노트로 이번 방학을 특별하게!"),
    ("body",     "  완성 후 도서 1권 대출까지 연결해 드립니다."),
    ("empty",    ""),
    ("body",     "  #광복절 #광복절행사 #독서노트 #나만의노트 #어린이도서관"),
    ("body",     "  #여름방학 #초등체험 #8월15일"),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("empty",    ""),
    ("subtitle", "[ 카드 4 ] 청소년·성인 행사 홍보 (8월 3주차 게시)"),
    ("empty",    ""),
    ("body",     "  [이미지 방향]"),
    ("body",     "  진지한 분위기의 독서 토론 장면 + 책 텍스처 배경"),
    ("body",     "  두 행사를 하나의 카드에 함께 소개"),
    ("empty",    ""),
    ("body",     "  [캡션 문구]"),
    ("body",     "  8월의 도서관, 함께 읽고 이야기 나눠요."),
    ("empty",    ""),
    ("body",     "  청소년 역사 북토크"),
    ("body",     "  8월 22일(토) 오후 2시 | 중·고교생 15명 | 1호실"),
    ("body",     "  지정 도서를 읽고, 전문 진행자와 함께하는 깊은 토론"),
    ("empty",    ""),
    ("body",     "  성인 여름 독서 살롱"),
    ("body",     "  8월 29일(토) 오후 2시 | 성인 15명 | 1호실"),
    ("body",     "  광복 81주년, 역사를 현재와 연결하는 독서 살롱"),
    ("empty",    ""),
    ("body",     "  신청: 홈페이지 또는 방문 접수"),
    ("empty",    ""),
    ("body",     "  #북토크 #독서살롱 #청소년독서 #성인독서 #역사읽기"),
    ("body",     "  #광복81주년 #도서관토론 #독서문화"),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("empty",    ""),
    ("subtitle", "[ 카드 5 ] 북큐레이션 홍보 (8월 1일 게시)"),
    ("empty",    ""),
    ("body",     "  [이미지 방향]"),
    ("body",     "  책들이 줄지어 꽂힌 서가 + 추천 도서 표지 목업(목업 3~4권)"),
    ("body",     "  어린이/성인 버전 각각 1장씩 제작"),
    ("empty",    ""),
    ("body",     "  [캡션 문구]"),
    ("body",     "  이번 달 사서 추천 도서"),
    ("empty",    ""),
    ("body",     "  [어린이] 여름방학에 읽는 우리 역사 이야기"),
    ("body",     "  친일, 독립운동, 근현대사를 어린이 눈높이로 담은 8권"),
    ("body",     "  어린이자료실에서 만나보세요!"),
    ("empty",    ""),
    ("body",     "  [성인] 해방 이후 우리가 읽어야 할 책들"),
    ("body",     "  광복 81주년, 해방 전후의 역사와 현재를 잇는 8권"),
    ("body",     "  종합자료실에서 만나보세요!"),
    ("empty",    ""),
    ("body",     "  #북큐레이션 #사서추천 #역사책 #광복절 #여름방학독서"),
    ("body",     "  #어린이책 #성인교양 #도서관"),
    ("empty",    ""),
    ("body",     "─────────────────────────────────────────────────────────"),
    ("empty",    ""),
    ("body",     "[ 운영 지침 ]"),
    ("body",     "o 게시 주기: 주 1~2회 (화·금 오전 10시~11시 최적)"),
    ("body",     "o 스토리 활용: 각 행사 마감 전날 리마인더 스토리 게시"),
    ("body",     "o 참여 유도: 댓글 이벤트 (참가 희망 행사 댓글 작성 시 우선 안내)"),
    ("body",     "o 통일 해시태그: #도서관 #공공도서관 #빛을향해읽다 #8월행사"),
    ("body",     "o 담당: 기획업무팀 기획담당"),
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
