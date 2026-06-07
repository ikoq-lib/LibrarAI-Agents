# -*- coding: utf-8 -*-
import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_6월_행사기획안.hwpx"

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
    return (f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" '
            f'pageBreak="0" columnBreak="0" merged="0">'
            f'<hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>')


# 문단 목록 구성
paragraphs = []
pid = 2  # id=1은 SECPR 고정


def add(text, para_pr=7, style=0, char_pr=5):
    global pid
    paragraphs.append(para(pid, text, para_pr, style, char_pr))
    pid += 1


def add_empty():
    global pid
    paragraphs.append(para_empty(pid))
    pid += 1


# ─── 제목 ───
add("2026년 6월 월간 행사 기획안", para_pr=2, style=0, char_pr=2)
add("초록을 읽다 — 지구와 나, 환경 독서의 달", para_pr=2, style=0, char_pr=3)
add_empty()
add("작성일: 2026년 4월 12일    담당: 기획업무팀 기획담당", para_pr=2, style=0, char_pr=0)
add_empty()

# ─── 행사 개요 ───
add("■ 행사 개요", para_pr=3, style=0, char_pr=3)
add("· 주제: 초록을 읽다 — 지구와 나, 환경 독서의 달")
add("· 기간: 2026년 6월 1일(월) ~ 6월 30일(화)")
add("· 장소: 도서관 내 각 강의실 및 자료실")
add("· 대상: 전 연령 이용자 (행사별 상이)")
add("· 총 예산: 410,000원 (상한 500,000원 이내)")
add_empty()
add("■ 주제 선정 이유", para_pr=3, style=0, char_pr=3)
add("· 6월 5일 세계 환경의 날(UN 지정) — 시의성 높은 환경 주제 부각")
add("· 장마 직전 자연 체감 시기 — 기후 변화를 직접 느끼는 계절적 맥락")
add("· 기후 위기 사회적 이슈 지속 부상 — 전 세대 공감 가능한 독서 주제")
add("· 5월 가족 독서의 달 주제와 차별화 — 월별 테마 연속성 확보")
add_empty()

# ─── 행사 1: 어린이 북큐레이션 ───
add("■ 1. 어린이 북큐레이션 — 지구를 지키는 책 탐험대", para_pr=3, style=0, char_pr=3)
add("· 기간: 6월 1일(월) ~ 6월 30일(화) 상시 전시")
add("· 대상: 유아·초등 전학년")
add("· 장소: 자료실 내 북큐레이션 코너")
add("· 예산: 0원 (기존 소장 자료 활용)")
add("· 내용: 환경·생태·기후 주제 그림책·동화 7권 선정 전시")
add("· 선정 도서:")
add("  1) 곰이 잠을 못 자는 이유")
add("  2) 쓰레기책")
add("  3) 마지막 나무")
add("  4) 이상한 날씨")
add("  5) 우리가 함께 만드는 작은 숲")
add("  6) 바다가 우리에게 말한다")
add("  7) 지구를 부탁해")
add_empty()

# ─── 행사 2: 성인 북큐레이션 ───
add("■ 2. 성인 북큐레이션 — 기후 시대를 사는 법", para_pr=3, style=0, char_pr=3)
add("· 기간: 6월 1일(월) ~ 6월 30일(화) 상시 전시")
add("· 대상: 성인 누구나")
add("· 장소: 자료실 내 북큐레이션 코너")
add("· 예산: 0원 (기존 소장 자료 활용)")
add("· 내용: 기후 위기·생태·지속가능성 관련 소설·에세이·비문학 7권 선정 전시")
add("· 선정 도서:")
add("  1) 우리가 날씨다")
add("  2) 지구 한계의 경계에서")
add("  3) 기후 위기와 불평등 사회")
add("  4) 채식주의자가 되기 전에 알아야 할 것들")
add("  5) 인류세")
add("  6) 2050 거주불능 지구")
add("  7) 조용한 혁명")
add_empty()

# ─── 행사 3: 어린이 참여① ───
add("■ 3. 어린이 참여① — 내가 만드는 지구 (환경 그림 엽서 만들기)", para_pr=3, style=0, char_pr=3)
add("· 일시: 2026년 6월 6일(토) 10:30 ~ 12:00")
add("· 장소: 2·3강의실")
add("· 대상: 초등 1~4학년 20명")
add("· 예산: 80,000원 (재료비)")
add("· 진행 순서:")
add("  ① 환경 그림책 낭독")
add("  ② 수채화 엽서 그리기")
add("  ③ 환경 다짐 문구 작성")
add("  ④ 완성 엽서 게시판 전시")
add("· 준비사항: 수채화 엽서용지, 물감세트 / 진행 사서 2인")
add_empty()

# ─── 행사 4: 어린이 참여② ───
add("■ 4. 어린이 참여② — 씨앗을 심는 도서관 (화분 만들기)", para_pr=3, style=0, char_pr=3)
add("· 일시: 2026년 6월 21일(일) 10:30 ~ 12:00")
add("· 장소: 2강의실")
add("· 대상: 초등 1~3학년 10팀 (가족 참여 가능)")
add("· 예산: 90,000원 (재료비)")
add("· 진행 순서:")
add("  ① 식물·자연 그림책 읽기")
add("  ② 화분 꾸미기")
add("  ③ 씨앗 파종 체험")
add("  ④ 완성 화분 집에 가져가기")
add("· 준비사항: 소형화분, 씨앗패키지, 상토, 꾸미기재료")
add_empty()

# ─── 행사 5: 성인 참여① ───
add("■ 5. 성인 참여① — 기후 책 살롱", para_pr=3, style=0, char_pr=3)
add("· 일시: 2026년 6월 13일(토) 14:00 ~ 16:00")
add("· 장소: 1강의실")
add("· 대상: 성인 12명")
add("· 예산: 130,000원 (강사비 100,000원 + 다과비 30,000원)")
add("· 지정 도서: 『2050 거주불능 지구』 (데이비드 월러스 웰즈) — 6월 1일부터 대출 가능")
add("· 진행 순서:")
add("  ① 참가자 소개 및 아이스브레이킹")
add("  ② 지정 도서 핵심 내용 요약 발표")
add("  ③ 토론 3문항 진행")
add("  ④ 실천 다짐 포스트잇 작성")
add("· 준비사항: 외부 퍼실리테이터 섭외 필요")
add_empty()

# ─── 행사 6: 성인 참여② ───
add("■ 6. 성인 참여② — 지구에게 쓰는 편지 (감성 글쓰기 워크숍)", para_pr=3, style=0, char_pr=3)
add("· 일시: 2026년 6월 27일(토) 14:00 ~ 16:00")
add("· 장소: 1강의실")
add("· 대상: 성인 15명")
add("· 예산: 110,000원 (강사비 100,000원 + 재료비 10,000원)")
add("· 진행 순서:")
add("  ① 환경 그림책 낭독")
add("  ② '30년 후의 지구에게' 편지 쓰기")
add("  ③ 완성 편지 자유 낭독 및 나눔")
add("· 준비사항: 외부 강사 섭외 필요 / 편지지, 봉투 등 재료 준비")
add_empty()

# ─── 예산 총괄 ───
add("■ 예산 총괄", para_pr=3, style=0, char_pr=3)
add("  ① 어린이 북큐레이션 (지구를 지키는 책 탐험대)     0원")
add("  ② 성인 북큐레이션 (기후 시대를 사는 법)           0원")
add("  ③ 어린이 참여① — 환경 그림 엽서 만들기          80,000원")
add("  ④ 어린이 참여② — 씨앗을 심는 도서관             90,000원")
add("  ⑤ 성인 참여① — 기후 책 살롱                   130,000원")
add("  ⑥ 성인 참여② — 지구에게 쓰는 편지              110,000원")
add("  ───────────────────────────────────────────────────────────")
add("  합계: 410,000원 (강사비 200,000원 + 재료비 210,000원)")
add("  ※ 예산 상한 500,000원 이내 집행")
add_empty()

# ─── 행사 일정 ───
add("■ 행사 일정표", para_pr=3, style=0, char_pr=3)
add("  6월 1일(월)   북큐레이션 전시 시작 (어린이·성인 동시)")
add("  6월 5일(금)   세계 환경의 날 — SNS·홈페이지 홍보 강화")
add("  6월 6일(토)   [행사③] 내가 만드는 지구 — 환경 그림 엽서 만들기 (10:30~12:00)")
add("  6월 13일(토)  [행사⑤] 기후 책 살롱 (14:00~16:00)")
add("  6월 21일(일)  [행사④] 씨앗을 심는 도서관 — 화분 만들기 (10:30~12:00)")
add("  6월 27일(토)  [행사⑥] 지구에게 쓰는 편지 — 감성 글쓰기 워크숍 (14:00~16:00)")
add("  6월 30일(화)  북큐레이션 전시 종료")
add_empty()
add_empty()
add("기획업무팀 기획담당", para_pr=2, style=0, char_pr=0)

# ─── section0.xml 조립 ───
body_paras = "\n".join(paragraphs)
section0 = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    f'<hp:sec {FULL_NS}>\n'
    f'{SECPR}\n'
    f'{body_paras}\n'
    f'</hp:sec>'
)

# ─── hwpx 생성 ───
with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
