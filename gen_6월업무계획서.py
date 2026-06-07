# -*- coding: utf-8 -*-
import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_6월_업무계획서.hwpx"

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
        f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" pageBreak="0" '
        f'columnBreak="0" merged="0"><hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'
    )


def build_section0(items):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR,
    ]
    pid = 2
    for item in items:
        if item is None:
            parts.append(para_empty(pid))
        elif isinstance(item, str):
            parts.append(para(pid, item))
        else:
            text, pp, s, cp = item
            parts.append(para(pid, text, pp, s, cp))
        pid += 1
    parts.append('</hs:sec>')
    return ''.join(parts)


# ── 문서 내용 정의 ──────────────────────────────────────────
paragraphs = []

# 제목
paragraphs.append(('2026년 6월 업무 계획서', 2, 0, 2))
paragraphs.append(None)
paragraphs.append(('담당: 기획업무팀 기획담당', 3, 0, 1))
paragraphs.append(('작성일: 2026. 5. 2.', 3, 0, 1))
paragraphs.append(None)

# 1. 월간 운영 목표
paragraphs.append(('1. 월간 운영 목표', 3, 0, 3))
paragraphs.append(None)
paragraphs.append(('월간 테마: 「초록을 읽다 - 지구와 나, 환경 독서의 달」', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('가. 세계 환경의 날(6. 5., UN 지정) 연계 환경 독서 문화 프로그램 운영', 7, 0, 5))
paragraphs.append(('나. 어린이·성인 대상 참여형 행사 4종, 북큐레이션 전시 2종 운영', 7, 0, 5))
paragraphs.append(('다. 2026년 5월 행사 결과보고서 작성 및 제출', 7, 0, 5))
paragraphs.append(('라. 7~8월 하계 행사 기획안 사전 준비', 7, 0, 5))
paragraphs.append(None)

# 2. 주요 행사 일정
paragraphs.append(('2. 주요 행사 일정', 3, 0, 3))
paragraphs.append(None)
paragraphs.append(('[표] 6월 행사 일정', 7, 0, 1))
paragraphs.append(('순  행사명  일시  대상·규모  예산(원)', 7, 0, 1))
paragraphs.append(('1  어린이 북큐레이션 - 지구를 지키는 책 탐험대  6. 1.(월)~6. 30.(화) 상시  어린이 자유 관람  0', 7, 0, 5))
paragraphs.append(('2  성인 북큐레이션 - 기후 시대를 사는 법  6. 1.(월)~6. 30.(화) 상시  성인 자유 관람  0', 7, 0, 5))
paragraphs.append(('3  내가 만드는 지구 (환경 그림 엽서 만들기)  6. 6.(토) 10:30~12:00  초등 1~4학년 20명  80,000', 7, 0, 5))
paragraphs.append(('4  기후 책 살롱  6. 13.(토) 14:00~16:00  성인 12명  130,000', 7, 0, 5))
paragraphs.append(('5  씨앗을 심는 도서관 (화분 만들기)  6. 21.(일) 10:30~12:00  초등 1~3학년 10팀  90,000', 7, 0, 5))
paragraphs.append(('6  지구에게 쓰는 편지 (감성 글쓰기 워크숍)  6. 27.(토) 14:00~16:00  성인 15명  110,000', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('소요예산 합계: 금410,000원 (강사비 200,000원 + 재료·운영비 210,000원)', 7, 0, 5))
paragraphs.append(None)

# 3. 주차별 세부 업무 계획
paragraphs.append(('3. 주차별 세부 업무 계획', 3, 0, 3))
paragraphs.append(None)

# 사전 준비
paragraphs.append(('가. 5월 중 사전 준비 (~2026. 5. 31.)', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('업무  내용  비고', 7, 0, 1))
paragraphs.append(('행사 홍보물 제작  홈페이지 배너, 인쇄물 포스터, SNS 카드뉴스  5월 중 배포 완료', 7, 0, 5))
paragraphs.append(('사전신청 접수  참여형 행사 4종 신청 페이지 개설 및 안내  도서관 홈페이지', 7, 0, 5))
paragraphs.append(('강사 섭외 및 계약  기후 책 살롱, 글쓰기 워크숍 외부강사 2명  강사비 각 100,000원', 7, 0, 5))
paragraphs.append(('재료 구입 품의  엽서 만들기·화분 만들기 재료비 구입 기안  총 170,000원', 7, 0, 5))
paragraphs.append(('지정도서 준비  기후 책 살롱 지정도서 「2050 거주불능 지구」  사서 대출 처리', 7, 0, 5))
paragraphs.append(None)

# 1주차
paragraphs.append(('나. 6월 1주차 (2026. 6. 1. ~ 6. 7.)', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('일자  업무  내용', 7, 0, 1))
paragraphs.append(('6. 1.(월)  북큐레이션 전시 설치  어린이·성인 전시대 설치, 선정도서 배치', 7, 0, 5))
paragraphs.append(('6. 1.(월)  세계 환경의 날 홍보 강화  SNS 홍보 게시물 발행 (6. 5. 예약 게시 포함)', 7, 0, 5))
paragraphs.append(('6. 6.(토)  내가 만드는 지구 운영  환경 그림 엽서 만들기, 초등 1~4학년 20명', 7, 0, 5))
paragraphs.append(('6. 7.(일)  5월 행사 결과보고서 작성  참가인원·만족도·집행예산 정리', 7, 0, 5))
paragraphs.append(None)

# 2주차
paragraphs.append(('다. 6월 2주차 (2026. 6. 8. ~ 6. 14.)', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('일자  업무  내용', 7, 0, 1))
paragraphs.append(('6. 8.(월)  5월 행사 결과보고서 제출  내부결재 기안', 7, 0, 5))
paragraphs.append(('6. 13.(토)  기후 책 살롱 운영  「2050 거주불능 지구」 독서 토론, 성인 12명', 7, 0, 5))
paragraphs.append(('6. 14.(일)  만족도 조사 수거·분석  3·4회차 행사 사후 만족도 확인', 7, 0, 5))
paragraphs.append(None)

# 3주차
paragraphs.append(('라. 6월 3주차 (2026. 6. 15. ~ 6. 21.)', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('일자  업무  내용', 7, 0, 1))
paragraphs.append(('6. 15.(월)  7·8월 행사 주제 후보 검토  여름방학·광복절 연계 테마 기획 착수', 7, 0, 5))
paragraphs.append(('6. 21.(일)  씨앗을 심는 도서관 운영  화분 만들기, 초등 1~3학년 10팀', 7, 0, 5))
paragraphs.append(None)

# 4주차
paragraphs.append(('마. 6월 4주차 (2026. 6. 22. ~ 6. 30.)', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('일자  업무  내용', 7, 0, 1))
paragraphs.append(('6. 27.(토)  지구에게 쓰는 편지 운영  감성 글쓰기 워크숍, 성인 15명', 7, 0, 5))
paragraphs.append(('6. 28.(일)  강사비 지급 기안 작성  외부강사 2명분 강사비 기안', 7, 0, 5))
paragraphs.append(('6. 30.(화)  6월 행사 결과보고서 작성 착수  참가인원·집행예산·사진 등 취합', 7, 0, 5))
paragraphs.append(('6. 30.(화)  7·8월 행사 기획안 초안 완성  내부 검토용 초안', 7, 0, 5))
paragraphs.append(None)

# 4. 예산 집행 계획
paragraphs.append(('4. 예산 집행 계획', 3, 0, 3))
paragraphs.append(None)
paragraphs.append(('항목  내역  금액(원)', 7, 0, 1))
paragraphs.append(('강사비  기후 책 살롱 강사 1인  100,000', 7, 0, 5))
paragraphs.append(('강사비  글쓰기 워크숍 강사 1인  100,000', 7, 0, 5))
paragraphs.append(('재료비  엽서 만들기 재료 (20명분)  80,000', 7, 0, 5))
paragraphs.append(('재료비  화분 만들기 재료 (10팀분)  90,000', 7, 0, 5))
paragraphs.append(('운영비  기후 책 살롱 다과비  40,000', 7, 0, 5))
paragraphs.append(('합  계    410,000', 7, 0, 5))
paragraphs.append(None)
paragraphs.append(('예산과목: 문화행사운영비', 7, 0, 5))
paragraphs.append(('집행 방식: 강사비 계좌이체, 재료비 구입품의 후 계산서 수취', 7, 0, 5))
paragraphs.append(None)

# 5. 기타 업무
paragraphs.append(('5. 기타 업무', 3, 0, 3))
paragraphs.append(None)
paragraphs.append(('업무  일정  내용', 7, 0, 1))
paragraphs.append(('도서관 이용통계 집계  6월 말  6월 이용자 수·대출 책 수·프로그램 참가자 수 통계', 7, 0, 5))
paragraphs.append(('희망도서 신청 접수  상시  이용자 희망도서 신청 취합 및 수서 부서 이관', 7, 0, 5))
paragraphs.append(('평생학습 프로그램 출석부 관리  상시  상반기 평생학습 프로그램 수료 처리 준비', 7, 0, 5))
paragraphs.append(('7·8월 행사 기획안 작성  6월 3~4주  여름방학·광복절 연계 행사 기획 초안 작성', 7, 0, 5))
paragraphs.append(None)

# 마무리
paragraphs.append(None)
paragraphs.append(('이상으로 2026년 6월 업무 계획을 보고합니다.', 2, 0, 5))
paragraphs.append(None)
paragraphs.append(('기획업무팀 기획담당', 2, 0, 5))

# ── 생성 ────────────────────────────────────────────────────
section0 = build_section0(paragraphs)

with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
