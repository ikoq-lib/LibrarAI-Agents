import zipfile, xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_5월_행사_보도자료.hwpx"

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


# 단락 ID 카운터
pid = [2]  # 1번은 SECPR이 사용


def P(text, para_pr=7, style=0, char_pr=5):
    p = para(pid[0], text, para_pr, style, char_pr)
    pid[0] += 1
    return p


def PE():
    p = para_empty(pid[0])
    pid[0] += 1
    return p


# 스타일 별칭
def title(text):       return P(text, para_pr=2, style=0, char_pr=2)   # 대제목 (가운데, 17pt)
def subhead_c(text):   return P(text, para_pr=2, style=0, char_pr=3)   # 소제목 가운데
def subhead_l(text):   return P(text, para_pr=3, style=0, char_pr=3)   # 소제목 좌측
def body(text):        return P(text, para_pr=7, style=0, char_pr=5)   # 일반 본문


paragraphs = [SECPR]

# ── 제목부 ──────────────────────────────────────────────────────────────────
paragraphs.append(title("보 도 자 료"))
paragraphs.append(PE())
paragraphs.append(body("배포일시: 2026년 4월 12일"))
paragraphs.append(body("담    당: 기획업무팀 기획담당"))
paragraphs.append(body("문    의: [전화번호]"))
paragraphs.append(PE())

# ── 헤드라인 3줄 ─────────────────────────────────────────────────────────────
paragraphs.append(subhead_c("[도서관명], 5월 한 달간 가족 독서 문화 행사 6종 운영"))
paragraphs.append(subhead_c("— \"함께 읽는 우리, 가족 독서의 달\" —"))
paragraphs.append(subhead_c("어린이부터 성인까지, 온 가족이 함께하는 독서 프로그램"))
paragraphs.append(PE())

# ── 리드 문단 ────────────────────────────────────────────────────────────────
paragraphs.append(body("[도서관명](관장 [관장명])은 5월 가정의 달을 맞이하여 오는 5월 1일(금)부터 31일(일)까지 한 달간 \"함께 읽는 우리 — 가족 독서의 달\"을 주제로 총 6종의 독서 문화 행사를 운영한다."))
paragraphs.append(PE())
paragraphs.append(body("이번 행사는 가족이 함께 책을 읽고 이야기를 나누는 문화를 도서관에서 시작하자는 취지로 기획되었으며, 어린이와 성인 모두를 아우르는 북큐레이션 전시 2건, 어린이 참여 행사 2건, 성인 참여 행사 2건으로 구성된다."))
paragraphs.append(PE())

# ── 행사 개요 ────────────────────────────────────────────────────────────────
paragraphs.append(subhead_l("■ 행사 개요"))
paragraphs.append(PE())
paragraphs.append(body("  ○ 주    제: 함께 읽는 우리 — 가족 독서의 달"))
paragraphs.append(body("  ○ 기    간: 2026년 5월 1일(금) ~ 5월 31일(일)"))
paragraphs.append(body("  ○ 장    소: [도서관명] 1강의실, 2·3강의실"))
paragraphs.append(body("  ○ 대    상: 어린이(초등 이하) 및 성인"))
paragraphs.append(body("  ○ 총 행사: 6종 (북큐레이션 2건 + 참여형 행사 4건)"))
paragraphs.append(body("  ○ 담    당: 기획업무팀 기획담당"))
paragraphs.append(PE())

# ── 행사별 상세 안내 ──────────────────────────────────────────────────────────
paragraphs.append(subhead_l("■ 행사별 상세 안내"))
paragraphs.append(PE())

# ① 어린이 북큐레이션
paragraphs.append(subhead_l("① 어린이 북큐레이션 — 엄마·아빠랑 같이 읽고 싶은 책"))
paragraphs.append(body("  ○ 기    간: 2026년 5월 1일(금) ~ 5월 31일(일) 상시 전시"))
paragraphs.append(body("  ○ 대    상: 어린이 전연령"))
paragraphs.append(body("  ○ 내    용: 세대 간 공감과 가족 대화를 이끄는 그림책·동화·소설 8권을 사서가 직접 선정하여 전시"))
paragraphs.append(body("  ○ 참가 방법: 별도 신청 없이 자유 관람"))
paragraphs.append(PE())

# ② 성인 북큐레이션
paragraphs.append(subhead_l("② 성인 북큐레이션 — 부모가 된다는 것"))
paragraphs.append(body("  ○ 기    간: 2026년 5월 1일(금) ~ 5월 31일(일) 상시 전시"))
paragraphs.append(body("  ○ 대    상: 성인 (부모, 예비부모)"))
paragraphs.append(body("  ○ 내    용: 가족 구조·부모 심리·세대 이해를 다각도로 조명하는 소설·에세이·비문학 7권을 사서가 직접 선정하여 전시"))
paragraphs.append(body("  ○ 참가 방법: 별도 신청 없이 자유 관람"))
paragraphs.append(PE())

# ③ 어린이날 편지 쓰기
paragraphs.append(subhead_l("③ 어린이날 편지 쓰기"))
paragraphs.append(body("  ○ 일    시: 2026년 5월 5일(화) 어린이날, 10:00~17:00 (자유 방문형)"))
paragraphs.append(body("  ○ 장    소: 2·3강의실"))
paragraphs.append(body("  ○ 대    상: 어린이 (초등 이하)"))
paragraphs.append(body("  ○ 내    용: 가족에게 전하는 마음을 편지와 그림으로 표현하는 행사로, 완성된 편지는 도서관 게시판에 전시됨"))
paragraphs.append(body("  ○ 예상 인원: 40명"))
paragraphs.append(body("  ○ 참가 방법: 당일 자유 방문 (사전 신청 불필요)"))
paragraphs.append(PE())

# ④ 우리 가족 이야기책 만들기
paragraphs.append(subhead_l("④ 우리 가족 이야기책 만들기"))
paragraphs.append(body("  ○ 일    시: 2026년 5월 9일(토) 14:00~16:00"))
paragraphs.append(body("  ○ 장    소: 2·3강의실"))
paragraphs.append(body("  ○ 대    상: 어린이 + 보호자 (가족 단위)"))
paragraphs.append(body("  ○ 내    용: 그림책을 함께 읽고 가족만의 이야기를 구성·토론한 뒤 미니북으로 직접 제작하고 발표하는 가족 참여형 프로그램"))
paragraphs.append(body("  ○ 예상 인원: 20명 (10가족)"))
paragraphs.append(body("  ○ 참가 방법: 사전 신청 (신청 방법: [홈페이지 URL] 또는 전화 [전화번호])"))
paragraphs.append(PE())

# ⑤ 감성 글쓰기 워크숍
paragraphs.append(subhead_l("⑤ 감성 글쓰기 워크숍"))
paragraphs.append(body("  ○ 일    시: 2026년 5월 16일(토) 14:00~16:00"))
paragraphs.append(body("  ○ 장    소: 1강의실"))
paragraphs.append(body("  ○ 대    상: 성인 20명"))
paragraphs.append(body("  ○ 내    용: 그림책 낭독을 시작으로 부모·자녀·가족을 주제로 한 감사 편지 쓰기 워크숍. 글쓰기 전문 강사 진행"))
paragraphs.append(body("  ○ 예상 인원: 20명"))
paragraphs.append(body("  ○ 참가 방법: 사전 신청 (신청 방법: [홈페이지 URL] 또는 전화 [전화번호])"))
paragraphs.append(PE())

# ⑥ 독서 토론 살롱
paragraphs.append(subhead_l("⑥ 독서 토론 살롱"))
paragraphs.append(body("  ○ 일    시: 2026년 5월 23일(토) 14:00~16:00"))
paragraphs.append(body("  ○ 장    소: 1강의실"))
paragraphs.append(body("  ○ 대    상: 성인 20명"))
paragraphs.append(body("  ○ 내    용: 사전 선정 도서를 함께 읽은 후, 세대·가족 관계를 주제로 사서 진행의 자유 토론 프로그램. 다과 제공"))
paragraphs.append(body("  ○ 예상 인원: 20명"))
paragraphs.append(body("  ○ 참가 방법: 사전 신청 (신청 방법: [홈페이지 URL] 또는 전화 [전화번호])"))
paragraphs.append(PE())

# ── 일정 한눈에 보기 ──────────────────────────────────────────────────────────
paragraphs.append(subhead_l("■ 행사 일정 한눈에 보기"))
paragraphs.append(PE())
paragraphs.append(body("  5/ 1(금)  북큐레이션 전시 시작 (어린이·성인 — 한 달간 상시)"))
paragraphs.append(body("  5/ 5(화)  어린이날 편지 쓰기 (자유 방문, 10:00~17:00)"))
paragraphs.append(body("  5/ 9(토)  우리 가족 이야기책 만들기 (14:00~16:00)"))
paragraphs.append(body("  5/16(토)  감성 글쓰기 워크숍 (14:00~16:00)"))
paragraphs.append(body("  5/23(토)  독서 토론 살롱 (14:00~16:00)"))
paragraphs.append(body("  5/31(일)  북큐레이션 전시 종료"))
paragraphs.append(PE())

# ── 관계자 코멘트 ──────────────────────────────────────────────────────────────
paragraphs.append(body("[도서관명] [관장명] 관장은 \"가정의 달 5월을 맞이해 온 가족이 도서관에서 함께 책을 읽고 이야기를 나눌 수 있는 다양한 프로그램을 마련했다\"며 \"어린이부터 성인까지 누구나 참여할 수 있으니 많은 관심과 참여를 바란다\"고 밝혔다."))
paragraphs.append(PE())

# ── 문의처 ─────────────────────────────────────────────────────────────────
paragraphs.append(body("기타 자세한 사항은 [도서관명] 홈페이지([홈페이지 URL]) 또는 전화([전화번호])로 문의하면 된다."))
paragraphs.append(PE())

# ── 붙임 ──────────────────────────────────────────────────────────────────
paragraphs.append(body("※ 붙임: 2026년 5월 월간 행사 기획안 1부.  끝."))

# ── XML 조립 ─────────────────────────────────────────────────────────────────
body_xml = "\n".join(paragraphs)
section0 = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    f'<hs:sec {FULL_NS} id="0">\n'
    f'<hs:subList>\n'
    f'{body_xml}\n'
    f'</hs:subList>\n'
    f'</hs:sec>'
)

# ── hwpx 생성 ─────────────────────────────────────────────────────────────────
with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
