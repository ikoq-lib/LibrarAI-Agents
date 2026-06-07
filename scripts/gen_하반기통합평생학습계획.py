# -*- coding: utf-8 -*-
import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_하반기_통합평생학습프로그램운영계획.hwpx"

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

def p_center(pid, text, char_pr=0):
    return p(pid, text, para_pr=2, style=0, char_pr=char_pr)

def p_title(pid, text):
    return p(pid, text, para_pr=2, style=0, char_pr=2)

def p_subtitle(pid, text):
    return p(pid, text, para_pr=3, style=0, char_pr=3)

def p_empty(pid):
    return (f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>')

def build_section0(parts_list):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR
    ]
    parts.extend(parts_list)
    parts.append('</hs:sec>')
    return ''.join(parts)

# ──────────────────────────────────────────────
# 문서 본문 구성
# ──────────────────────────────────────────────
pid = 2
paras = []

# ===기안문시작===
paras.append(p_empty(pid)); pid += 1
paras.append(p_title(pid, "기 안 문")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "기 관 명:  ○○도서관",                   para_pr=3, char_pr=1)); pid += 1
paras.append(p(pid, "문서번호:  평생학습-2026-하반기-001",      para_pr=3, char_pr=1)); pid += 1
paras.append(p(pid, "시행일자:  2026년 4월 18일",             para_pr=3, char_pr=1)); pid += 1
paras.append(p(pid, "결  재:   기획업무팀장",                  para_pr=3, char_pr=1)); pid += 1
paras.append(p(pid, "담  당:   기획업무팀 기획담당",            para_pr=3, char_pr=1)); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p_title(pid, "2026년 하반기 평생학습 프로그램 운영 계획 기안")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "1. 관련 근거")); pid += 1
paras.append(p(pid, "   가. 도서관법 제38조(도서관의 평생교육)")); pid += 1
paras.append(p(pid, "   나. 2026년도 ○○도서관 운영계획")); pid += 1
paras.append(p(pid, "   다. 평생학습 연간 예산 편성 기준 (강사비 15,000,000원, 재료비 3,000,000원)")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "2. 기안 목적")); pid += 1
paras.append(p(pid, "   2026년 하반기(7월~12월) 성인 및 어린이 평생학습 프로그램을 통합 편성하여 지역 주민의")); pid += 1
paras.append(p(pid, "   평생학습 기회를 확대하고, 생애주기별 맞춤형 교육서비스를 제공하고자 함.")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "3. 세부 계획: 별첨 참조")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "4. 소요 예산")); pid += 1
paras.append(p(pid, "   - 강사비 하반기 배정 가능액: 13,400,000원 (연간 15,000,000원 - 여름방학 기편성 1,600,000원)")); pid += 1
paras.append(p(pid, "   - 재료비 하반기 배정 가능액:  2,765,000원 (연간  3,000,000원 - 여름방학 기편성   235,000원)")); pid += 1
paras.append(p(pid, "   - 하반기 실집행 계획 강사비: 11,100,000원")); pid += 1
paras.append(p(pid, "   - 하반기 실집행 계획 재료비:  1,640,000원")); pid += 1
paras.append(p(pid, "   - 하반기 합계:               12,740,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "위와 같이 기안합니다.")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p_center(pid, "2026년 4월 18일")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p_center(pid, "기획업무팀 기획담당 (서명)")); pid += 1
paras.append(p_empty(pid)); pid += 1
# ===기안문끝===

# ===첨부시작===
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "━" * 55, para_pr=2, char_pr=1)); pid += 1
paras.append(p_title(pid, "【첨부】 2026년 하반기 평생학습 프로그램 운영 세부 계획")); pid += 1
paras.append(p(pid, "━" * 55, para_pr=2, char_pr=1)); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 1. 개요 ──
paras.append(p_subtitle(pid, "1. 운영 개요")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  ○ 운영 기간 : 2026년 7월 1일(수) ~ 2026년 12월 19일(토)")); pid += 1
paras.append(p(pid, "  ○ 대상 및 정원")); pid += 1
paras.append(p(pid, "    - 성인 프로그램 : 19세 이상 성인, 강좌별 20명 이내")); pid += 1
paras.append(p(pid, "    - 어린이 프로그램 : 5~13세 아동, 강좌별 10명 이내")); pid += 1
paras.append(p(pid, "  ○ 강의실 배정")); pid += 1
paras.append(p(pid, "    - 1호실(20명) : 성인 프로그램 전용")); pid += 1
paras.append(p(pid, "    - 2호실(10명) : 어린이 프로그램 A그룹 전용")); pid += 1
paras.append(p(pid, "    - 3호실(10명) : 어린이 프로그램 B·C그룹 전용")); pid += 1
paras.append(p(pid, "  ○ 강사비 기준 : 100,000원/회 (50,000원/시간 × 2시간)")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 2. 프로그램 구성 총괄 ──
paras.append(p_subtitle(pid, "2. 프로그램 구성 총괄 (하반기, 여름방학 프로그램 제외)")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  ┌──────────────────────────────────────────────────────────────────────────┐")); pid += 1
paras.append(p(pid, "  │ 구분   │ 강좌명                    │ 대상     │ 강의실 │ 기간          │ 횟수 │")); pid += 1
paras.append(p(pid, "  ├──────────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 성인①  │ 생활 POP 캘리그라피        │ 성인     │ 1호실  │ 9.3~10.22(목) │ 8회  │")); pid += 1
paras.append(p(pid, "  │ 성인②  │ 독서 글쓰기 워크숍         │ 성인     │ 1호실  │ 9.5~10.24(토) │ 8회  │")); pid += 1
paras.append(p(pid, "  │ 성인③  │ 스마트폰 사진·영상 편집    │ 성인     │ 1호실  │ 10.7~11.25(수)│ 8회  │")); pid += 1
paras.append(p(pid, "  │ 성인④  │ 우쿨렐레 입문             │ 성인     │ 1호실  │ 10.8~11.26(목)│ 8회  │")); pid += 1
paras.append(p(pid, "  ├──────────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 어린이① │ 코딩·메이킹 탐험대(초급)  │ 8~10세  │ 3호실  │ 9.5~10.24(토) │ 8회  │")); pid += 1
paras.append(p(pid, "  │ 어린이② │ 그림책 영어 스토리텔링    │ 5~7세   │ 2호실  │ 9.5~10.24(토) │ 8회  │")); pid += 1
paras.append(p(pid, "  │ 어린이③ │ 독서창작 북아트(중급)     │ 9~13세  │ 3호실  │ 10.7~11.25(수)│ 8회  │")); pid += 1
paras.append(p(pid, "  └──────────────────────────────────────────────────────────────────────────┘")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  ※ 여름방학 프로그램(그림책 창작 A그룹 / 과학 탐정단 B그룹, 7.14~8.6) 별도 운영 중")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 3. 성인 프로그램 세부 ──
paras.append(p_subtitle(pid, "3. 성인 평생학습 프로그램 세부 계획")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 성인①
paras.append(p(pid, "  [성인①] 생활 POP 캘리그라피")); pid += 1
paras.append(p(pid, "  - 대상 : 성인 20명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 1호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 9. 3.(목) ~ 10. 22.(목), 매주 목요일, 10:00~12:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : POP 글씨체 기초~중급, 감성 카드 제작, 캘리그라피 소품 응용")); pid += 1
paras.append(p(pid, "  - 강사 자격 : POP·캘리그라피 관련 자격증 소지자, 문화센터 강의 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 200,000원 (POP 마커, 전용지, 카드 재료 등)")); pid += 1
paras.append(p(pid, "  - 소계 : 1,000,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 성인②
paras.append(p(pid, "  [성인②] 독서 글쓰기 워크숍")); pid += 1
paras.append(p(pid, "  - 대상 : 성인 20명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 1호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 9. 5.(토) ~ 10. 24.(토), 매주 토요일, 14:00~16:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : 도서 선정 독서, 감상 글쓰기, 독서 에세이 완성 및 소책자 제작")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 문예창작·국어국문 전공 또는 글쓰기 지도 전문가, 성인 대상 강의 경력 2년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 120,000원 (소책자 제본, 필기류 등)")); pid += 1
paras.append(p(pid, "  - 소계 : 920,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 성인③
paras.append(p(pid, "  [성인③] 스마트폰 사진·영상 편집 클래스")); pid += 1
paras.append(p(pid, "  - 대상 : 성인 20명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 1호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 10. 7.(수) ~ 11. 25.(수), 매주 수요일, 10:00~12:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : 스마트폰 카메라 활용, 사진 보정 앱(Lightroom Mobile), 릴스·쇼츠 편집 실습")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 디지털 미디어·영상 분야 전문가, 시니어 대상 스마트폰 강의 경력 우대")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 40,000원 (유인물, 스마트폰 거치대 등 소모품)")); pid += 1
paras.append(p(pid, "  - 소계 : 840,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 성인④
paras.append(p(pid, "  [성인④] 우쿨렐레 입문")); pid += 1
paras.append(p(pid, "  - 대상 : 성인 20명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 1호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 10. 8.(목) ~ 11. 26.(목), 매주 목요일, 14:00~16:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : 우쿨렐레 기초 코드(C, Am, F, G7), 동요·팝송 연주, 소규모 발표 무대")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 우쿨렐레·기타 연주 전공자 또는 실기 지도 자격 보유, 문화센터 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 50,000원 (악보집 인쇄, 줄·피크 소모품)")); pid += 1
paras.append(p(pid, "  - 소계 : 850,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

paras.append(p(pid, "  ▶ 성인 프로그램 소계 : 강사비 3,200,000원 + 재료비 410,000원 = 3,610,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 4. 어린이 프로그램 세부 ──
paras.append(p_subtitle(pid, "4. 어린이 평생학습 프로그램 세부 계획")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 어린이①
paras.append(p(pid, "  [어린이①] 코딩·메이킹 탐험대 (초급)")); pid += 1
paras.append(p(pid, "  - 대상 : 초등학교 2~4학년(8~10세) 10명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 3호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 9. 5.(토) ~ 10. 24.(토), 매주 토요일, 10:00~12:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : 언플러그드 코딩 이해 → 스크래치 기초 → 마이크로비트 미션 → 작품 발표회")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 소프트웨어·컴퓨터교육 전공 또는 SW 강사 자격(정보교육사 등), 초등 대상 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 320,000원 (마이크로비트 부품, 공작 소모품 등 / 10명 기준)")); pid += 1
paras.append(p(pid, "  - 소계 : 1,120,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 어린이②
paras.append(p(pid, "  [어린이②] 그림책 영어 스토리텔링")); pid += 1
paras.append(p(pid, "  - 대상 : 유아·유치원생(5~7세) 10명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 2호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 9. 5.(토) ~ 10. 24.(토), 매주 토요일, 11:00~13:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : 영어 그림책 읽기·듣기, 이야기 속 어휘 놀이, 플래시카드 만들기, 짧은 스토리 발표")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 영어교육·TESOL 자격 보유, 유아 영어 강의 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 250,000원 (영어 그림책 10권, 플래시카드 재료 등)")); pid += 1
paras.append(p(pid, "  - 소계 : 1,050,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 어린이③
paras.append(p(pid, "  [어린이③] 독서창작 북아트 (중급)")); pid += 1
paras.append(p(pid, "  - 대상 : 초등학교 3~6학년(9~13세) 10명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 3호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 10. 7.(수) ~ 11. 25.(수), 매주 수요일, 15:00~17:00, 총 8회")); pid += 1
paras.append(p(pid, "  - 내용 : 도서 선정 후 독후감 쓰기 → 북아트 기법(아코디언·팝업) → 나만의 책 완성·전시")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 독서지도사·북아트 전문 강사 자격 보유, 초등 강의 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 8회 = 800,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 200,000원 (제본 재료, 색지, 장식 소모품 등)")); pid += 1
paras.append(p(pid, "  - 소계 : 1,000,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

paras.append(p(pid, "  ▶ 어린이 프로그램 소계 : 강사비 2,400,000원 + 재료비 770,000원 = 3,170,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 5. 동절기 특별 프로그램 ──
paras.append(p_subtitle(pid, "5. 동절기 특별 프로그램 (11월~12월)")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 동절기 성인
paras.append(p(pid, "  [동절기 성인] 나의 한 해를 담는 사진 에세이")); pid += 1
paras.append(p(pid, "  - 대상 : 성인 20명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 1호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 11. 7.(토) ~ 12. 12.(토), 매주 토요일, 14:00~16:00, 총 6회")); pid += 1
paras.append(p(pid, "  - 내용 : 한 해 사진 정리·편집, 에세이 쓰기, 포토북 완성 (연말 결산 콘셉트)")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 6회 = 600,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 180,000원 (포토북 인쇄, 유인물 등)")); pid += 1
paras.append(p(pid, "  - 소계 : 780,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 동절기 어린이
paras.append(p(pid, "  [동절기 어린이] 겨울 창작 미술 (5~10세)")); pid += 1
paras.append(p(pid, "  - 대상 : 5~10세 어린이 10명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 2호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 11. 7.(토) ~ 12. 12.(토), 매주 토요일, 10:00~12:00, 총 6회")); pid += 1
paras.append(p(pid, "  - 내용 : 계절 주제 미술 창작(눈·별·동물), 콜라주·수채화·점토 활동, 작품 전시")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 아동미술지도사, 어린이 미술 강의 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 6회 = 600,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 180,000원 (미술 소모품, 점토, 색지 등)")); pid += 1
paras.append(p(pid, "  - 소계 : 780,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# 동절기 청소년
paras.append(p(pid, "  [동절기 청소년] 진로독서 토크 콘서트 (11~13세)")); pid += 1
paras.append(p(pid, "  - 대상 : 초등 5학년~중학교 1학년(11~13세) 10명 이내")); pid += 1
paras.append(p(pid, "  - 강의실 : 3호실")); pid += 1
paras.append(p(pid, "  - 일정 : 2026. 11. 14.(토) ~ 12. 19.(토), 매주 토요일, 14:00~16:00, 총 6회")); pid += 1
paras.append(p(pid, "  - 내용 : 진로 관련 도서 선정 독서 → 직업·꿈 탐색 토론 → 나의 미래 발표 책 만들기")); pid += 1
paras.append(p(pid, "  - 강사 자격 : 진로상담사·독서지도사 자격 보유, 청소년 대상 강의 경력 1년 이상")); pid += 1
paras.append(p(pid, "  - 강사비 : 100,000원 × 6회 = 600,000원")); pid += 1
paras.append(p(pid, "  - 재료비 : 100,000원 (도서 구입 지원, 제본 재료)")); pid += 1
paras.append(p(pid, "  - 소계 : 700,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

paras.append(p(pid, "  ▶ 동절기 프로그램 소계 : 강사비 1,800,000원 + 재료비 460,000원 = 2,260,000원")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 6. 강의실 배정 일정표 ──
paras.append(p_subtitle(pid, "6. 강의실 배정 현황 (충돌 검토)")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  ┌────────────────────────────────────────────────────────────────────────────┐")); pid += 1
paras.append(p(pid, "  │ 강의실 │ 요일   │ 시간대      │ 운영 강좌                            │ 기간          │")); pid += 1
paras.append(p(pid, "  ├────────────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 1호실  │ 목요일 │ 10:00~12:00 │ 성인① 생활 POP 캘리그라피            │ 9.3~10.22     │")); pid += 1
paras.append(p(pid, "  │ 1호실  │ 토요일 │ 14:00~16:00 │ 성인② 독서 글쓰기 워크숍             │ 9.5~10.24     │")); pid += 1
paras.append(p(pid, "  │ 1호실  │ 수요일 │ 10:00~12:00 │ 성인③ 스마트폰 사진·영상 편집        │ 10.7~11.25    │")); pid += 1
paras.append(p(pid, "  │ 1호실  │ 목요일 │ 14:00~16:00 │ 성인④ 우쿨렐레 입문                  │ 10.8~11.26    │")); pid += 1
paras.append(p(pid, "  │ 1호실  │ 토요일 │ 14:00~16:00 │ 동절기 성인 사진 에세이               │ 11.7~12.12    │")); pid += 1
paras.append(p(pid, "  ├────────────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 2호실  │ 화·목  │ 10:00~11:30 │ 여름방학 그림책 창작(A, 5~7세)       │ 7.14~8.6      │")); pid += 1
paras.append(p(pid, "  │ 2호실  │ 토요일 │ 11:00~13:00 │ 어린이② 그림책 영어 스토리텔링       │ 9.5~10.24     │")); pid += 1
paras.append(p(pid, "  │ 2호실  │ 토요일 │ 10:00~12:00 │ 동절기 어린이 겨울 창작 미술          │ 11.7~12.12    │")); pid += 1
paras.append(p(pid, "  ├────────────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 3호실  │ 화·목  │ 14:00~16:00 │ 여름방학 과학 탐정단(B, 8~10세)      │ 7.14~8.6      │")); pid += 1
paras.append(p(pid, "  │ 3호실  │ 토요일 │ 10:00~12:00 │ 어린이① 코딩·메이킹 탐험대           │ 9.5~10.24     │")); pid += 1
paras.append(p(pid, "  │ 3호실  │ 수요일 │ 15:00~17:00 │ 어린이③ 독서창작 북아트              │ 10.7~11.25    │")); pid += 1
paras.append(p(pid, "  │ 3호실  │ 토요일 │ 14:00~16:00 │ 동절기 청소년 진로독서 토크           │ 11.14~12.19   │")); pid += 1
paras.append(p(pid, "  └────────────────────────────────────────────────────────────────────────────┘")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  ※ 강의실 충돌 없음 확인 완료 (동일 호실·동일 요일·동일 시간대 중복 없음)")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 7. 예산 총괄 ──
paras.append(p_subtitle(pid, "7. 하반기 예산 총괄")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  [강사비]")); pid += 1
paras.append(p(pid, "  ┌──────────────────────────────────────────────────────────────────────┐")); pid += 1
paras.append(p(pid, "  │ 구분                  │ 횟수 │ 단가      │ 강사비       │ 재료비    │ 소계       │")); pid += 1
paras.append(p(pid, "  ├──────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ [이미 편성] 여름방학 A그룹  │  8회 │ 100,000원 │   800,000원  │  100,000원 │   900,000원 │")); pid += 1
paras.append(p(pid, "  │ [이미 편성] 여름방학 B그룹  │  8회 │ 100,000원 │   800,000원  │  135,000원 │   935,000원 │")); pid += 1
paras.append(p(pid, "  ├──────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 성인① 캘리그라피           │  8회 │ 100,000원 │   800,000원  │  200,000원 │ 1,000,000원 │")); pid += 1
paras.append(p(pid, "  │ 성인② 독서 글쓰기           │  8회 │ 100,000원 │   800,000원  │  120,000원 │   920,000원 │")); pid += 1
paras.append(p(pid, "  │ 성인③ 스마트폰 편집         │  8회 │ 100,000원 │   800,000원  │   40,000원 │   840,000원 │")); pid += 1
paras.append(p(pid, "  │ 성인④ 우쿨렐레              │  8회 │ 100,000원 │   800,000원  │   50,000원 │   850,000원 │")); pid += 1
paras.append(p(pid, "  │ 어린이① 코딩·메이킹         │  8회 │ 100,000원 │   800,000원  │  320,000원 │ 1,120,000원 │")); pid += 1
paras.append(p(pid, "  │ 어린이② 영어 스토리텔링     │  8회 │ 100,000원 │   800,000원  │  250,000원 │ 1,050,000원 │")); pid += 1
paras.append(p(pid, "  │ 어린이③ 북아트              │  8회 │ 100,000원 │   800,000원  │  200,000원 │ 1,000,000원 │")); pid += 1
paras.append(p(pid, "  │ 동절기 성인 사진 에세이      │  6회 │ 100,000원 │   600,000원  │  180,000원 │   780,000원 │")); pid += 1
paras.append(p(pid, "  │ 동절기 어린이 창작 미술      │  6회 │ 100,000원 │   600,000원  │  180,000원 │   780,000원 │")); pid += 1
paras.append(p(pid, "  │ 동절기 청소년 진로독서       │  6회 │ 100,000원 │   600,000원  │  100,000원 │   700,000원 │")); pid += 1
paras.append(p(pid, "  ├──────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 하반기 신규 편성 소계        │ 74회 │           │ 7,400,000원  │1,640,000원 │ 9,040,000원 │")); pid += 1
paras.append(p(pid, "  ├──────────────────────────────────────────────────────────────────────┤")); pid += 1
paras.append(p(pid, "  │ 여름방학 기편성 포함 하반기 합계 │ 90회 │       │ 9,000,000원  │1,875,000원 │10,875,000원 │")); pid += 1
paras.append(p(pid, "  └──────────────────────────────────────────────────────────────────────┘")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  [연간 예산 집행 현황 (하반기 계획 포함)]")); pid += 1
paras.append(p(pid, "  - 강사비 연간 예산 : 15,000,000원")); pid += 1
paras.append(p(pid, "  - 강사비 하반기 집행 계획 : 9,000,000원 (여름방학 1,600,000원 포함)")); pid += 1
paras.append(p(pid, "  - 상반기 미편성 잔액 : 6,000,000원 (향후 특강·긴급 프로그램 예비비 활용)")); pid += 1
paras.append(p(pid, "  - 재료비 연간 예산 : 3,000,000원")); pid += 1
paras.append(p(pid, "  - 재료비 하반기 집행 계획 : 1,875,000원 (여름방학 235,000원 포함)")); pid += 1
paras.append(p(pid, "  - 재료비 잔액 : 1,125,000원 (예비비)")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 8. 추진 일정 ──
paras.append(p_subtitle(pid, "8. 추진 일정")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  - 2026. 04. 18. : 하반기 통합 프로그램 기획안 기안 (현재)")); pid += 1
paras.append(p(pid, "  - 2026. 05. 11. : 강사 채용 공고 (하반기 전체 강좌 통합 공고)")); pid += 1
paras.append(p(pid, "  - 2026. 06. 15. : 강사 면접 및 선정 완료")); pid += 1
paras.append(p(pid, "  - 2026. 06. 22. : 수강생 모집 공고 (9~10월 강좌)")); pid += 1
paras.append(p(pid, "  - 2026. 07. 13. : 수강생 모집 마감 (9~10월 강좌)")); pid += 1
paras.append(p(pid, "  - 2026. 09. 01. : 1차 강좌 개강 준비 완료")); pid += 1
paras.append(p(pid, "  - 2026. 09. 03. : 성인① 캘리그라피 개강")); pid += 1
paras.append(p(pid, "  - 2026. 09. 05. : 성인②·어린이①② 개강")); pid += 1
paras.append(p(pid, "  - 2026. 09. 10. : 수강생 모집 공고 (10~12월 강좌)")); pid += 1
paras.append(p(pid, "  - 2026. 09. 30. : 수강생 모집 마감 (10~12월 강좌)")); pid += 1
paras.append(p(pid, "  - 2026. 10. 07. : 성인③·어린이③ 개강")); pid += 1
paras.append(p(pid, "  - 2026. 10. 08. : 성인④ 우쿨렐레 개강")); pid += 1
paras.append(p(pid, "  - 2026. 11. 07. : 동절기 성인·어린이 개강")); pid += 1
paras.append(p(pid, "  - 2026. 11. 14. : 동절기 청소년 진로독서 개강")); pid += 1
paras.append(p(pid, "  - 2026. 12. 19. : 전체 강좌 종강 및 결과 취합")); pid += 1
paras.append(p(pid, "  - 2026. 12. 31. : 하반기 운영 결과보고서 제출")); pid += 1
paras.append(p_empty(pid)); pid += 1

# ── 9. 기타 ──
paras.append(p_subtitle(pid, "9. 기타 사항")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "  ○ 어린이 프로그램은 보호자 동의서 징구 및 안전교육 실시 후 진행")); pid += 1
paras.append(p(pid, "  ○ 수강 신청은 도서관 홈페이지 및 방문 접수 병행")); pid += 1
paras.append(p(pid, "  ○ 강사 계약 시 청렴서약서·개인정보보호 서약서 동시 징구")); pid += 1
paras.append(p(pid, "  ○ 어린이 강사는 아동학대 예방 교육 이수 확인서 제출 의무화")); pid += 1
paras.append(p(pid, "  ○ 수강 정원 미달(50% 미만) 시 해당 강좌 폐강 후 예산 반납")); pid += 1
paras.append(p(pid, "  ○ 강좌 운영 만족도 조사는 매 강좌 종강일에 실시하며 결과보고에 반영")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p_center(pid, "- 끝 -")); pid += 1
paras.append(p_empty(pid)); pid += 1
paras.append(p(pid, "담당자: 기획업무팀 기획담당")); pid += 1
# ===첨부끝===

section0 = build_section0(paras)

with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
