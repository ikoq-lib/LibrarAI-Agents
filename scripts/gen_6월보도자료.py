import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_6월_행사_보도자료.hwpx"

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
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escaped}</hp:t></hp:run></hp:p>'
    )


def para_empty(pid):
    return (
        f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'
    )


# 단락 ID 카운터
pid = [2]


def p(text, para_pr=7, style=0, char_pr=5):
    node = para(pid[0], text, para_pr, style, char_pr)
    pid[0] += 1
    return node


def pe():
    node = para_empty(pid[0])
    pid[0] += 1
    return node


# ── 보도자료 본문 단락 구성 ──────────────────────────────────────────

paragraphs = []

# 대제목: 보 도 자 료
paragraphs.append(p("보  도  자  료", para_pr=2, style=0, char_pr=2))
paragraphs.append(pe())

# 배포 정보 (일반 본문)
paragraphs.append(p("배포일시: 2026년 4월 12일(일)"))
paragraphs.append(p("담    당: 기획업무팀 기획담당"))
paragraphs.append(p("문    의: [도서관명] 홈페이지([홈페이지 URL]) 또는 전화([전화번호])"))
paragraphs.append(pe())

# 헤드라인 (소제목, 가운데)
paragraphs.append(p("[도서관명], 6월 한 달간 환경 독서 문화 행사 6종 운영", para_pr=2, style=0, char_pr=3))
# 부제 (소제목, 가운데)
paragraphs.append(p("「초록을 읽다 — 지구와 나, 환경 독서의 달」", para_pr=2, style=0, char_pr=3))
paragraphs.append(pe())

# 리드 문단
paragraphs.append(p("    [도서관명](관장 [관장명])은 2026년 6월 1일(월)부터 6월 30일(화)까지 한 달간 '초록을 읽다 — 지구와 나, 환경 독서의 달'을 주제로 어린이부터 성인까지 참여할 수 있는 환경 독서 문화 행사 6종을 운영한다. 이번 행사는 북큐레이션 2건과 참여형 프로그램 4건으로 구성되며 총 예산은 410,000원이다."))
paragraphs.append(pe())

# ■ 행사 개요
paragraphs.append(p("■ 행사 개요", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  ○ 기    간: 2026년 6월 1일(월) ~ 6월 30일(화)"))
paragraphs.append(p("  ○ 장    소: [도서관명] 및 각 행사별 지정 공간"))
paragraphs.append(p("  ○ 행사 구성: 북큐레이션 2건 + 참여형 프로그램 4건 (총 6종)"))
paragraphs.append(p("  ○ 총 예 산: 410,000원"))
paragraphs.append(p("  ○ 주    관: [도서관명] 기획업무팀"))
paragraphs.append(pe())

# ■ 행사별 상세 안내
paragraphs.append(p("■ 행사별 상세 안내", para_pr=3, style=0, char_pr=3))
paragraphs.append(pe())

# ① 어린이 북큐레이션
paragraphs.append(p("① 어린이 북큐레이션 — 지구를 지키는 책 탐험대", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 기    간: 2026년 6월 한 달 상시"))
paragraphs.append(p("  - 대    상: 어린이 이용자"))
paragraphs.append(p("  - 내    용: 환경·생태 주제 어린이 추천 도서 큐레이션 전시 및 대출 서비스"))
paragraphs.append(p("  - 비    용: 무료 (사전신청 불필요)"))
paragraphs.append(pe())

# ② 성인 북큐레이션
paragraphs.append(p("② 성인 북큐레이션 — 기후 시대를 사는 법", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 기    간: 2026년 6월 한 달 상시"))
paragraphs.append(p("  - 대    상: 성인 이용자"))
paragraphs.append(p("  - 내    용: 기후위기·환경 관련 성인 추천 도서 큐레이션 전시 및 대출 서비스"))
paragraphs.append(p("  - 비    용: 무료 (사전신청 불필요)"))
paragraphs.append(pe())

# ③ 환경 그림 엽서 만들기
paragraphs.append(p("③ 환경 그림 엽서 만들기", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 일    시: 2026년 6월 6일(토) 10:30 ~ 12:00"))
paragraphs.append(p("  - 대    상: 초등학교 1~4학년"))
paragraphs.append(p("  - 내    용: 환경 그림책을 읽고 지구에 보내는 그림 엽서 창작 활동"))
paragraphs.append(p("  - 신청방법: 사전신청 (홈페이지 또는 방문 접수)"))
paragraphs.append(pe())

# ④ 씨앗을 심는 도서관
paragraphs.append(p("④ 씨앗을 심는 도서관 — 화분 만들기", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 일    시: 2026년 6월 21일(일) 10:30 ~ 12:00"))
paragraphs.append(p("  - 대    상: 초등학교 1~3학년"))
paragraphs.append(p("  - 내    용: 식물 관련 그림책 낭독 후 직접 씨앗을 심어 화분 만들기 체험"))
paragraphs.append(p("  - 신청방법: 사전신청 (홈페이지 또는 방문 접수)"))
paragraphs.append(pe())

# ⑤ 기후 책 살롱
paragraphs.append(p("⑤ 기후 책 살롱", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 일    시: 2026년 6월 13일(토) 14:00 ~ 16:00"))
paragraphs.append(p("  - 대    상: 성인 12명 (선착순)"))
paragraphs.append(p("  - 지정도서: 『2050 거주불능 지구』"))
paragraphs.append(p("  - 내    용: 기후위기를 다룬 지정 도서 독후 토론 및 이야기 나눔"))
paragraphs.append(p("  - 신청방법: 사전신청 (홈페이지 또는 방문 접수)"))
paragraphs.append(pe())

# ⑥ 지구에게 쓰는 편지
paragraphs.append(p("⑥ 지구에게 쓰는 편지 — 감성 글쓰기 워크숍", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 일    시: 2026년 6월 27일(토) 14:00 ~ 16:00"))
paragraphs.append(p("  - 대    상: 성인 15명 (선착순)"))
paragraphs.append(p("  - 내    용: 환경 에세이·시 낭독 후 지구에게 쓰는 편지 형식의 감성 글쓰기 워크숍"))
paragraphs.append(p("  - 신청방법: 사전신청 (홈페이지 또는 방문 접수)"))
paragraphs.append(pe())

# ■ 관계자 코멘트
paragraphs.append(p("■ 관계자 코멘트", para_pr=3, style=0, char_pr=3))
paragraphs.append(p('    [도서관명] 관장은 "6월 환경의 달을 맞아 어린이부터 성인까지 함께 지구를 생각하는 독서 문화 행사를 마련했다. 책을 통해 환경 문제를 새롭게 바라보는 계기가 되길 바란다"고 밝혔다.'))
paragraphs.append(pe())

# ■ 신청 안내
paragraphs.append(p("■ 신청 안내", para_pr=3, style=0, char_pr=3))
paragraphs.append(p("  - 신청기간: 각 행사 1주일 전부터 접수 시작"))
paragraphs.append(p("  - 신청방법: [도서관명] 홈페이지([홈페이지 URL]) 온라인 신청 또는 도서관 방문 접수"))
paragraphs.append(p("  - 문    의: [전화번호]"))
paragraphs.append(pe())

# 끝맺음
paragraphs.append(p("붙임: 2026년 6월 월간 행사 기획안 1부.  끝."))
paragraphs.append(pe())


# ── section0.xml 조립 ──────────────────────────────────────────────

body = "".join(paragraphs)

section0 = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<hp:sec {FULL_NS}>'
    f'{SECPR}'
    f'{body}'
    f'</hp:sec>'
)

# ── hwpx 파일 생성 ─────────────────────────────────────────────────

with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"완료: {OUTPUT}")
