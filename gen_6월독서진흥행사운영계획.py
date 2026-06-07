# -*- coding: utf-8 -*-
import zipfile
import xml.sax.saxutils as saxutils

# 기본 보고서 템플릿 사용 (검증된 파일)
TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_6월_독서진흥행사_운영계획.hwpx"

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


def esc(text):
    return saxutils.escape(text)


def para(pid, text, para_pr=7, style=0, char_pr=5):
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}"><hp:t>{esc(text)}</hp:t></hp:run></hp:p>'
    )


def empty(pid):
    return (
        f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" pageBreak="0" '
        f'columnBreak="0" merged="0"><hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'
    )


def build(items):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR,
    ]
    pid = 2
    for item in items:
        if item is None:
            parts.append(empty(pid))
        else:
            text, pp, s, cp = item
            parts.append(para(pid, text, pp, s, cp))
        pid += 1
    parts.append('</hs:sec>')
    return ''.join(parts)


# ── 단축 함수 ────────────────────────────────────────────────
T  = lambda t: (t, 7, 0, 5)    # 기본 본문
TL = lambda t: (t, 3, 0, 1)    # 왼쪽 정렬 작은 글자
TC = lambda t: (t, 2, 0, 2)    # 가운데 큰 제목
TH = lambda t: (t, 3, 0, 3)    # 소제목 (섹션 헤더)
TB = lambda t: (t, 7, 0, 1)    # 표 헤더 / 구분선
# ────────────────────────────────────────────────────────────

doc = []

# ── 문서 제목 ────────────────────────────────────────────────
doc.append(None)
doc.append(TC('2026년 6월 독서진흥행사 운영 계획'))
doc.append(None)
doc.append(TL('경상남도교육청 창녕도서관'))
doc.append(None)
doc.append(None)

# ── Ⅰ. 목적 ─────────────────────────────────────────────────
doc.append(TH('Ⅰ. 목적'))
doc.append(None)
doc.append(T(' 지역민 누구나 책과 함께 즐길 수 있는 다채로운 독서문화서비스 제공'))
doc.append(T(' 세계 환경의 날(6. 5.) 연계 환경 독서 문화 프로그램 운영으로 생태·환경 인식 확산'))
doc.append(T(' 도서관에서의 다양한 독서 경험을 통해 독서 습관 형성 및 도서관 이용 생활화 유도'))
doc.append(None)

# ── Ⅱ. 관련근거 ─────────────────────────────────────────────
doc.append(TH('Ⅱ. 관련근거'))
doc.append(None)
doc.append(T(' 「도서관법」 제32조 및 「독서문화진흥법」 제9조'))
doc.append(T(' 경상남도교육청 창녕도서관-73(2026.1.6.) "2026년 주요업무계획 수립"'))
doc.append(None)

# ── Ⅲ. 운영 방침 ────────────────────────────────────────────
doc.append(TH('Ⅲ. 운영 방침'))
doc.append(None)
doc.append(T(' 계층별·대상별 다양한 독서, 체험, 전시 행사 등으로 구성하여 운영'))
doc.append(T(' 어린이 대상 프로그램은 어린이자료실 담당 사서 주관하에 협력하여 운영'))
doc.append(T(' 독서문화 격차를 해소하고 지역민과 함께하는 독서진흥행사 운영'))
doc.append(T(' 세계 환경의 날 등 환경 기념일과 연계하여 환경 독서문화 행사 운영'))
doc.append(None)

# ── Ⅳ. 행사 개요 ────────────────────────────────────────────
doc.append(TH('Ⅳ. 행사 개요'))
doc.append(None)
doc.append(T(' 운영기간: 2026. 6. 1.(월) ~ 6. 30.(화)'))
doc.append(T(' 운영장소: 창녕도서관 각 자료실 및 별관 강좌실'))
doc.append(T(' 운영대상: 어린이, 청소년, 성인 등 관심 있는 창녕군민 누구나'))
doc.append(T(' 운영내용: [초록을 읽다 - 지구와 나] 등 6개 독서/전시/체험행사'))
doc.append(T(' 주    관: 경상남도교육청 창녕도서관'))
doc.append(None)

# ── Ⅴ. 세부 프로그램 ─────────────────────────────────────────
doc.append(TH('Ⅴ. 세부 프로그램'))
doc.append(None)

# 1. 어린이 북큐레이션
doc.append(T('1. [전시] 어린이 북큐레이션 - 지구를 지키는 책 탐험대'))
doc.append(T(' 가. 기간: 6. 1.(월) ~ 6. 30.(화)'))
doc.append(T(' 나. 장소: 어린이자료실'))
doc.append(T(' 다. 대상: 도서관 이용자 (어린이)'))
doc.append(T(' 라. 내용: 지구·환경 주제 관련 어린이 도서를 선정하여 전시 및 서평 게시'))
doc.append(None)

# 2. 성인 북큐레이션
doc.append(T('2. [전시] 성인 북큐레이션 - 기후 시대를 사는 법'))
doc.append(T(' 가. 기간: 6. 1.(월) ~ 6. 30.(화)'))
doc.append(T(' 나. 장소: 종합자료실'))
doc.append(T(' 다. 대상: 도서관 이용자 (성인)'))
doc.append(T(' 라. 내용: 기후 위기·환경 주제 성인 추천 도서를 선정하여 전시 및 서평 게시'))
doc.append(None)

# 3. 엽서 만들기
doc.append(T('3. [체험] 내가 만드는 지구 (환경 그림 엽서 만들기)'))
doc.append(T(' 가. 일시: 6. 6.(토) 10:30~12:00'))
doc.append(T(' 나. 장소: 어린이자료실'))
doc.append(T(' 다. 대상: 초등 1~4학년 20명 (사전 신청)'))
doc.append(T(' 라. 내용: 세계 환경의 날(6. 5.) 연계, 지구 환경을 주제로 그림 엽서 만들기 체험'))
doc.append(None)

# 4. 기후 책 살롱
doc.append(T('4. [독서] 기후 책 살롱'))
doc.append(T(' 가. 일시: 6. 13.(토) 14:00~16:00'))
doc.append(T(' 나. 장소: 별관 문화강좌실 2'))
doc.append(T(' 다. 대상: 성인 12명 (사전 신청)'))
doc.append(T(' 라. 내용: 지정도서 「2050 거주불능 지구」를 읽고 함께 이야기 나누는 독서 토론 모임'))
doc.append(None)

# 5. 화분 만들기
doc.append(T('5. [체험] 씨앗을 심는 도서관 (화분 만들기)'))
doc.append(T(' 가. 일시: 6. 21.(일) 10:30~12:00'))
doc.append(T(' 나. 장소: 어린이자료실'))
doc.append(T(' 다. 대상: 초등 1~3학년 10팀 (사전 신청)'))
doc.append(T(' 라. 내용: 화분을 직접 만들어 씨앗을 심는 자연 관찰 체험, 관련 환경 도서 함께 소개'))
doc.append(None)

# 6. 글쓰기 워크숍
doc.append(T('6. [독서] 지구에게 쓰는 편지 (감성 글쓰기 워크숍)'))
doc.append(T(' 가. 일시: 6. 27.(토) 14:00~16:00'))
doc.append(T(' 나. 장소: 별관 문화강좌실 1'))
doc.append(T(' 다. 대상: 성인 15명 (사전 신청)'))
doc.append(T(' 라. 내용: 환경 이슈를 주제로 지구에게 보내는 편지 쓰기 감성 글쓰기 워크숍'))
doc.append(None)

# ── Ⅵ. 소요 예산 ─────────────────────────────────────────────
doc.append(TH('Ⅵ. 소요 예산'))
doc.append(None)
doc.append(T(' 소요 금액: 금410,000원(금사십일만원)'))
doc.append(T(' 산출 내역'))
doc.append(None)
doc.append(TB('구분(행사명)                        산출 내역                                금액(원)   비고'))
doc.append(TB('─────────────────────────────────────────────────────────────────────────'))
doc.append(T('내가 만드는 지구 (엽서 만들기)      재료비 20명×4,000원                       80,000'))
doc.append(T('기후 책 살롱                        강사비 100,000원 + 다과비 30,000원        130,000'))
doc.append(T('씨앗을 심는 도서관 (화분 만들기)    재료비 10팀×9,000원                       90,000'))
doc.append(T('지구에게 쓰는 편지 (글쓰기 워크숍)  강사비 100,000원 + 재료비 10,000원       110,000'))
doc.append(TB('─────────────────────────────────────────────────────────────────────────'))
doc.append(T('합          계                                                              410,000'))
doc.append(None)
doc.append(T(' 예산 과목: 독서문화 프로그램 운영, 도서관운영, 도서관독서진흥행사'))
doc.append(None)

# ── Ⅶ. 홍보 ─────────────────────────────────────────────────
doc.append(TH('Ⅶ. 홍    보'))
doc.append(None)
doc.append(T(' 경남교육홍보관, 지역 언론사 등 보도자료 홍보'))
doc.append(T(' 관내 게시판 및 도서관 홈페이지, SNS, DID 홍보'))
doc.append(T(' 현수막 제작: 도서관 게시대 및 외부 게시대'))
doc.append(None)

# ── Ⅷ. 기대 효과 ────────────────────────────────────────────
doc.append(TH('Ⅷ. 기대 효과'))
doc.append(None)
doc.append(T(' 세계 환경의 날 연계 독서진흥행사 운영으로 지역민들의 환경 인식 제고 및 도서관 이용 유도'))
doc.append(T(' 어린이·성인 모두 참여할 수 있는 프로그램 운영으로 세대 간 환경 독서 문화 확산'))
doc.append(T(' 이용자와 소통하는 친근한 도서관 이미지 구축으로 지역주민의 도서관 이용 생활화 유도'))
doc.append(None)

# ── 생성 ─────────────────────────────────────────────────────
section0 = build(doc)

with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
