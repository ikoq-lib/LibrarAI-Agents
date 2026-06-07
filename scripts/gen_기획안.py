import zipfile
import shutil
import os
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_5월_행사기획안.hwpx"

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


# 문단 목록 구성
paragraphs = []
pid = 2  # 1번은 SECPR

def add(text, para_pr=7, char_pr=5):
    global pid
    paragraphs.append(para(pid, text, para_pr=para_pr, char_pr=char_pr))
    pid += 1

def add_empty():
    global pid
    paragraphs.append(para_empty(pid))
    pid += 1

def add_section(text):
    """섹션 헤더 — 소제목 좌측 정렬"""
    global pid
    paragraphs.append(para(pid, text, para_pr=3, char_pr=3))
    pid += 1

def add_title(text):
    """대제목 — 가운데 정렬, 17pt"""
    global pid
    paragraphs.append(para(pid, text, para_pr=2, char_pr=2))
    pid += 1

def add_subtitle(text):
    """부제목 — 소제목 가운데 정렬"""
    global pid
    paragraphs.append(para(pid, text, para_pr=2, char_pr=3))
    pid += 1


# ── 제목 영역 ──────────────────────────────────────────
add_title("2026년 5월 월간 행사 기획안")
add_subtitle("함께 읽는 우리 \u2014 가족 독서의 달")
add_empty()
add("작성일: 2026년 4월 12일        담당: 기획업무팀 기획담당")
add_empty()
add_empty()

# ── 행사 개요 ──────────────────────────────────────────
add_section("\u25a0 행사 개요")
add("\u2500" * 54)
add("  \u25cb 주제    : 함께 읽는 우리 \u2014 가족 독서의 달")
add("  \u25cb 기간    : 2026년 5월 1일(금) ~ 5월 31일(일)")
add("  \u25cb 장소    : 1강의실(성인 20명) / 2\u00b73강의실(어린이 각 10명)")
add("  \u25cb 총 행사 : 6개 (북큐레이션 2건 + 참여형 행사 4건)")
add("  \u25cb 총 예산 : 427,400원")
add_empty()
add_empty()

# ── 북큐레이션 ──────────────────────────────────────────
add_section("\u25a0 북큐레이션 (상시 전시 \u2014 5월 한 달간)")
add("\u2500" * 54)
add_empty()
add("\u2460 어린이 북큐레이션 \u2014 엄마\u00b7아빠랑 같이 읽고 싶은 책 (8권)")
add("  \u2022 대상    : 어린이 전연령")
add("  \u2022 형태    : 상시 전시")
add("  \u2022 내용    : 세대 간 공감과 가족 대화를 이끄는 그림책\u00b7동화\u00b7소설 8권 선정\u00b7전시")
add("  \u2022 예산    : 0원 (사서 직접 선정\u00b7전시)")
add_empty()
add("\u2461 성인 북큐레이션 \u2014 부모가 된다는 것 (7권)")
add("  \u2022 대상    : 성인 (부모, 예비부모)")
add("  \u2022 형태    : 상시 전시")
add("  \u2022 내용    : 가족 구조\u00b7부모 심리\u00b7세대 이해를 다각도로 조명하는 소설\u00b7에세이\u00b7비문학 7권 선정\u00b7전시")
add("  \u2022 예산    : 0원 (사서 직접 선정\u00b7전시)")
add_empty()
add_empty()

# ── 어린이 참여형 행사 ──────────────────────────────────────────
add_section("\u25a0 어린이 참여형 행사")
add("\u2500" * 54)
add_empty()
add("\u2462 어린이날 편지 쓰기")
add("  \u2022 일시    : 2026년 5월 5일(화) 어린이날, 10:00~17:00 (자유 방문형)")
add("  \u2022 장소    : 2\u00b73강의실")
add("  \u2022 대상    : 어린이 (초등 이하)")
add("  \u2022 내용    : 가족에게 쓰는 편지 + 그림 그리기, 완성된 편지는 게시판에 전시")
add("  \u2022 예상 인원: 40명")
add("  \u2022 예산    : 70,000원 (편지지\u00b7색연필\u00b7꾸미기 재료비)")
add("  \u2022 준비 사항: 편지지 50매, 색연필 세트, 스티커, 게시판 설치, 사서 2인 배치")
add_empty()
add("\u2463 우리 가족 이야기책 만들기")
add("  \u2022 일시    : 2026년 5월 9일(토) 14:00~16:00")
add("  \u2022 장소    : 2\u00b73강의실")
add("  \u2022 대상    : 어린이 + 보호자 (가족 단위)")
add("  \u2022 내용    : 그림책 함께 읽기 \u2192 가족 이야기 구성 토론 \u2192 미니북 제작 및 발표")
add("  \u2022 예상 인원: 20명 (10가족)")
add("  \u2022 예산    : 86,000원 (미니북 제작 재료비)")
add("  \u2022 준비 사항: 미니북 키트 10세트, 그림책 선정, 사서 진행 대본 준비")
add_empty()
add_empty()

# ── 성인 참여형 행사 ──────────────────────────────────────────
add_section("\u25a0 성인 참여형 행사")
add("\u2500" * 54)
add_empty()
add("\u2464 감성 글쓰기 워크숍")
add("  \u2022 일시    : 2026년 5월 16일(토) 14:00~16:00")
add("  \u2022 장소    : 1강의실")
add("  \u2022 대상    : 성인 20명")
add("  \u2022 내용    : 그림책 낭독 \u2192 부모\u00b7자녀\u00b7가족을 주제로 한 감사 편지 쓰기 워크숍")
add("  \u2022 강사    : 외부 강사 1인 (글쓰기 전문 강사)")
add("  \u2022 예상 인원: 20명")
add("  \u2022 예산    : 139,000원 (강사비 100,000원 + 재료비 39,000원)")
add("  \u2022 준비 사항: 강사 섭외 및 계약, 편지지\u00b7펜 세트, 그림책 1권, 참가자 모집 공고")
add_empty()
add("\u2465 독서 토론 살롱")
add("  \u2022 일시    : 2026년 5월 23일(토) 14:00~16:00")
add("  \u2022 장소    : 1강의실")
add("  \u2022 대상    : 성인 20명")
add("  \u2022 내용    : 선정 도서 1권 공통 독서 후 세대\u00b7가족 관계를 주제로 한 자유 토론")
add("  \u2022 진행    : 사서 직접 진행 (강사비 없음)")
add("  \u2022 예상 인원: 20명")
add("  \u2022 예산    : 132,400원 (도서 구매비 + 다과비)")
add("  \u2022 준비 사항: 선정 도서 구매(20권), 토론 질문지 준비, 다과 준비, 참가자 사전 신청")
add_empty()
add_empty()

# ── 예산 총괄 ──────────────────────────────────────────
add_section("\u25a0 예산 총괄")
add("\u2500" * 54)
add("  행사명                        강사비      재료비      합계")
add("  \u2500" * 27)
add("  \u2460 어린이 북큐레이션              0원          0원          0원")
add("  \u2461 성인 북큐레이션                0원          0원          0원")
add("  \u2462 어린이날 편지 쓰기             0원     70,000원     70,000원")
add("  \u2463 우리 가족 이야기책 만들기      0원     86,000원     86,000원")
add("  \u2464 감성 글쓰기 워크숍       100,000원     39,000원    139,000원")
add("  \u2465 독서 토론 살롱                 0원    132,400원    132,400원")
add("  \u2500" * 27)
add("  합  계                    100,000원    327,400원    427,400원")
add_empty()
add_empty()

# ── 행사 일정 달력 ──────────────────────────────────────────
add_section("\u25a0 행사 일정 달력")
add("\u2500" * 54)
add("  5/ 1(금)  \u25b6 북큐레이션 전시 시작 (어린이\u00b7성인)")
add("  5/ 5(화)  \u25b6 [행사\u2462] 어린이날 편지 쓰기 (자유 방문)")
add("  5/ 9(토)  \u25b6 [행사\u2463] 우리 가족 이야기책 만들기")
add("  5/16(토)  \u25b6 [행사\u2464] 감성 글쓰기 워크숍")
add("  5/23(토)  \u25b6 [행사\u2465] 독서 토론 살롱")
add("  5/31(일)  \u25b6 북큐레이션 전시 종료")
add_empty()

# ── XML 조립 ──────────────────────────────────────────
body = SECPR + "".join(paragraphs)
section0_xml = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<hp:sec {FULL_NS}>'
    f'{body}'
    f'</hp:sec>'
)

# 템플릿 복사 후 section0.xml 교체
shutil.copy2(TEMPLATE, OUTPUT)

with zipfile.ZipFile(OUTPUT, 'r') as zin:
    names = zin.namelist()

# section0.xml 경로 확인
section_name = None
for n in names:
    if 'section0.xml' in n or 'Section0.xml' in n:
        section_name = n
        break

if section_name is None:
    # 후보 탐색
    for n in names:
        if 'section' in n.lower() and n.endswith('.xml'):
            print(f"후보: {n}")
    raise RuntimeError("section0.xml을 찾을 수 없습니다. 위 후보를 확인하세요.")

print(f"교체 대상: {section_name}")

# 임시 파일로 교체
TEMP = OUTPUT + ".tmp"
with zipfile.ZipFile(OUTPUT, 'r') as zin:
    with zipfile.ZipFile(TEMP, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == section_name:
                zout.writestr(item, section0_xml.encode('utf-8'))
            else:
                zout.writestr(item, zin.read(item.filename))

os.replace(TEMP, OUTPUT)
print(f"완료: {OUTPUT}")
print(f"총 문단 수: {pid - 1}")
