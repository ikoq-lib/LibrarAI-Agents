# -*- coding: utf-8 -*-
import zipfile
import xml.sax.saxutils as saxutils

# 기본 보고서 템플릿 사용 (검증된 파일)
TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_9월_독서진흥행사_운영계획.hwpx"

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
doc.append(TC('2026년 9월 독서진흥행사 운영 계획'))
doc.append(None)
doc.append(TC('[ 책의 달, 다시 읽는 가을 ]'))
doc.append(None)
doc.append(TL('경상남도교육청 창녕도서관'))
doc.append(None)
doc.append(None)

# ── Ⅰ. 목적 ─────────────────────────────────────────────────
doc.append(TH('Ⅰ. 목적'))
doc.append(None)
doc.append(T(' 「독서문화진흥법」에 따른 독서의 달(9월)을 맞아 집중 독서진흥행사를 운영하여 지역민의 독서 의욕 고취'))
doc.append(T(' 책·도서관을 소재로 한 계층별 독서 체험 활동을 통해 독서 습관 형성 및 도서관 이용 생활화 유도'))
doc.append(T(' 소장 자료를 활용한 북큐레이션 전시로 장서 활용률을 제고하고 이용자의 독서 선택권 확대'))
doc.append(None)

# ── Ⅱ. 관련근거 ─────────────────────────────────────────────
doc.append(TH('Ⅱ. 관련근거'))
doc.append(None)
doc.append(T(' 「도서관법」 제32조(공공도서관의 업무)'))
doc.append(T(' 「독서문화진흥법」 제9조(독서 진흥에 관한 사업) 및 제12조(독서의 달)'))
doc.append(T(' 경상남도교육청 창녕도서관-73(2026. 1. 6., 「2026년 주요업무계획 수립」)'))
doc.append(None)

# ── Ⅲ. 운영 방침 ────────────────────────────────────────────
doc.append(TH('Ⅲ. 운영 방침'))
doc.append(None)
doc.append(T(' 독서의 달 취지에 맞추어 책·읽기·도서관을 공통 소재로 6개 행사를 구성하여 운영'))
doc.append(T(' 북큐레이션 도서는 신규 구입 없이 관내 소장 자료로 구성하여 예산 절감 및 장서 활용률 제고'))
doc.append(T(' 어린이 대상 프로그램은 어린이자료실 담당 사서 주관하에 협력하여 운영'))
doc.append(T(' 추석 연휴(9. 24.~9. 26.)를 제외한 주말에 참여형 행사를 균등 배치하여 참여율 확보'))
doc.append(None)

# ── Ⅳ. 행사 개요 ────────────────────────────────────────────
doc.append(TH('Ⅳ. 행사 개요'))
doc.append(None)
doc.append(T(' 운영기간: 2026. 9. 1.(화) ~ 9. 30.(수)'))
doc.append(T(' 운영장소: 창녕도서관 각 자료실 및 별관 강좌실'))
doc.append(T(' 운영대상: 어린이, 청소년, 성인 등 관심 있는 창녕군민 누구나'))
doc.append(T(' 운영내용: [책의 달, 다시 읽는 가을] 등 전시 2종·체험 4종 총 6개 독서진흥행사'))
doc.append(T(' 소요금액: 금400,000원(금사십만원)'))
doc.append(T(' 예산과목: 독서문화프로그램운영-3.도서관독서진흥행사(기초,자체)-1)독서진흥행사'))
doc.append(T(' 주    관: 경상남도교육청 창녕도서관'))
doc.append(None)
# ── Ⅴ. 세부 프로그램 ─────────────────────────────────────────
doc.append(TH('Ⅴ. 세부 프로그램'))
doc.append(None)

doc.append(TB('1. [전시] 가을, 책이 익어가는 자리 (어린이 북큐레이션)'))
doc.append(T('  가. 대    상: 유아 ~ 초등학생 및 보호자'))
doc.append(T('  나. 기    간: 2026. 9. 1.(화) ~ 9. 30.(수) 상시'))
doc.append(T('  다. 장    소: 어린이자료실 전시대'))
doc.append(T('  라. 내    용: 책·도서관을 소재로 한 소장 그림책·동화 8종 전시 및 서가 안내'))
doc.append(T('  마. 전시도서: 책 먹는 여우의 가을 이야기(주니어김영사) / 고양이 도서관(고래책빵) /'))
doc.append(T('               도서관에서 생긴 일(다그림책) / 우리가 책을 펼치면(노란상상) /'))
doc.append(T('               곧 책이 열립니다(웅진주니어) / 책 읽는 고양이 고고 선생 1(길벗스쿨) /'))
doc.append(T('               누구나 환영해! 개구리 책방(천개의바람) / 읽지 마! 도서관(킨더랜드)'))
doc.append(T('  바. 소요예산: 없음(소장 자료 및 기존 전시대 활용)'))
doc.append(None)

doc.append(TB('2. [전시] 다시 읽는 가을 (성인 북큐레이션)'))
doc.append(T('  가. 대    상: 청소년 및 성인'))
doc.append(T('  나. 기    간: 2026. 9. 1.(화) ~ 9. 30.(수) 상시'))
doc.append(T('  다. 장    소: 종합자료실 전시대'))
doc.append(T('  라. 내    용: 독서법·독서에세이·도서관 소재 소설 등 소장 자료 8종 전시'))
doc.append(T('  마. 전시도서: 다시 시작하는 평생 독서법(더퀘스트) / 읽지 못하는 사람의 미래(유유) /'))
doc.append(T('               청춘의 독서(웅진지식하우스) / 책 읽고 떠들기(북트리거) /'))
doc.append(T('               책 읽는 시민이 답이다(사회평론) / 우리동네 도서관(사유와공감) /'))
doc.append(T('               겹쳐진 도서관(TXTY) / 책, 읽는 재미 말고(유유)'))
doc.append(T('  바. 소요예산: 없음(소장 자료 및 기존 전시대 활용)'))
doc.append(None)

doc.append(TB('3. [체험] 내 마음의 한 문장 - 필사 책갈피 만들기'))
doc.append(T('  가. 대    상: 초등학교 1~4학년 20명(사전 신청)'))
doc.append(T('  나. 일    시: 2026. 9. 5.(토) 10:30 ~ 12:00'))
doc.append(T('  다. 장    소: 별관 강좌실 2·3호실(각 10명)'))
doc.append(T('  라. 내    용: 좋아하는 책에서 한 문장을 고르고 손글씨로 옮겨 적어 나만의 책갈피 제작'))
doc.append(T('               (10:30 도서 고르기 → 11:00 문장 필사 및 꾸미기 → 11:40 코팅·완성 및 소감 나누기)'))
doc.append(T('  마. 진    행: 어린이자료실 담당 사서 자체 진행(외부 강사 없음)'))
doc.append(T('  바. 준 비 물: 책갈피 원지, 코팅지, 펀치, 리본끈, 색연필, 네임펜'))
doc.append(T('  사. 소요예산: 금80,000원(재료비, 일반수용비)'))
doc.append(T('  아. 홍보포인트: 준비물 없이 몸만 오면 되는 무료 체험 / 완성품을 바로 가져갈 수 있음'))
doc.append(None)

doc.append(TB('4. [체험] 하루 사서 - 어린이 사서 체험 교실'))
doc.append(T('  가. 대    상: 초등학교 3~6학년 20명(사전 신청)'))
doc.append(T('  나. 일    시: 2026. 9. 19.(토) 10:30 ~ 12:00'))
doc.append(T('  다. 장    소: 별관 강좌실 2·3호실 및 어린이자료실'))
doc.append(T('  라. 내    용: 청구기호 읽는 법과 서가 배열 원리를 배우고 직접 자료를 찾아 정리하는 체험'))
doc.append(T('               (10:30 도서관과 사서의 일 → 11:00 청구기호 찾기 미션 → 11:40 나의 추천도서 카드 작성)'))
doc.append(T('  마. 진    행: 어린이자료실 담당 사서 자체 진행(외부 강사 없음)'))
doc.append(T('  바. 준 비 물: 사서 이름표(목걸이형), 미션 활동지, 추천도서 카드, 수료증, 기념품'))
doc.append(T('  사. 소요예산: 금70,000원(재료비, 일반수용비)'))
doc.append(T('  아. 홍보포인트: 진로 체험과 연계 가능 / 참가자가 작성한 추천도서 카드를 자료실에 전시'))
doc.append(None)

doc.append(TB('5. [체험] 가을 독서 살롱 - 다시 읽는 그 책'))
doc.append(T('  가. 대    상: 성인 15명(사전 신청)'))
doc.append(T('  나. 일    시: 2026. 9. 12.(토) 14:00 ~ 16:00'))
doc.append(T('  다. 장    소: 별관 강좌실 1호실'))
doc.append(T('  라. 지정도서: 『우리동네 도서관』(차인표 장편소설, 사유와공감)'))
doc.append(T('  마. 내    용: 지정도서를 미리 읽고 모여 함께 이야기하는 독서 토론 모임'))
doc.append(T('               (14:00 도입 및 인사 → 14:20 발제 → 14:50 자유 토론 → 15:40 마무리)'))
doc.append(T('  바. 진    행: 외부 강사 1명(진행·발제), 2시간 1회'))
doc.append(T('  사. 준 비 물: 지정도서 대출용 복본 10권(도서구입비 별도 집행), 다과, 명패'))
doc.append(T('  아. 소요예산: 금120,000원(강사수당 100,000원 + 다과 20,000원)'))
doc.append(T('  자. 홍보포인트: 지정도서를 도서관에서 빌려주므로 책값 부담 없음 / 도서관이 배경인 소설'))
doc.append(None)

doc.append(TB('6. [체험] 인생 책 한 권 - 서평 쓰기 워크숍'))
doc.append(T('  가. 대    상: 성인 15명(사전 신청)'))
doc.append(T('  나. 일    시: 2026. 9. 20.(일) 14:00 ~ 16:00'))
doc.append(T('  다. 장    소: 별관 강좌실 1호실'))
doc.append(T('  라. 내    용: 각자의 인생 책 한 권을 가져와 짧은 서평을 완성하는 글쓰기 워크숍'))
doc.append(T('               (14:00 좋은 서평의 조건 → 14:40 개별 집필 → 15:20 낭독 및 합평 → 15:50 마무리)'))
doc.append(T('  마. 진    행: 외부 강사 1명(글쓰기 강사), 2시간 1회'))
doc.append(T('  바. 준 비 물: 독서노트 15권, 필기구, 완성 서평 게시용 보드'))
doc.append(T('  사. 소요예산: 금130,000원(강사수당 100,000원 + 재료비 30,000원)'))
doc.append(T('  아. 홍보포인트: 완성한 서평을 자료실 게시판에 전시 / 독서동아리 신규 회원 유입 경로로 활용'))
doc.append(None)
