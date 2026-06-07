import zipfile
import xml.sax.saxutils as saxutils

TEMPLATE = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUTPUT = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_여름방학_어린이평생학습_프로그램운영계획.hwpx"

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

SECPR = (
    '<hp:p id="1" paraPrIDRef="29" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
    '<hp:run charPrIDRef="0">'
    '<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" '
    'outlineShapeIDRef="1" memoShapeIDRef="1" textVerticalWidthHead="0" masterPageCnt="0">'
    '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>'
    '<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
    '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" '
    'border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/>'
    '<hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/>'
    '<hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY">'
    '<hp:margin header="4251" footer="4251" gutter="0" left="5669" right="5669" top="4251" bottom="4251"/>'
    '</hp:pagePr>'
    '<hp:footNotePr>'
    '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
    '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="EACH_COLUMN" beneathText="0"/>'
    '</hp:footNotePr>'
    '<hp:endNotePr>'
    '<hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/>'
    '<hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="END_OF_DOCUMENT" beneathText="0"/>'
    '</hp:endNotePr>'
    '<hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '<hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '<hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" '
    'headerInside="0" footerInside="0" fillArea="PAPER">'
    '<hp:offset left="1417" right="1417" top="1417" bottom="1417"/>'
    '</hp:pageBorderFill>'
    '</hp:secPr>'
    '<hp:ctrl>'
    '<hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/>'
    '</hp:ctrl>'
    '</hp:run>'
    '</hp:p>'
)


def para(pid, text, para_pr=7, style=0, char_pr=5):
    escaped = saxutils.escape(text)
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="{style}" '
        f'pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="{char_pr}"><hp:t>{escaped}</hp:t></hp:run></hp:p>'
    )


def para_title(pid, text):
    return para(pid, text, para_pr=2, style=0, char_pr=2)


def para_subtitle(pid, text):
    return para(pid, text, para_pr=3, style=0, char_pr=3)


def para_center(pid, text, char_pr=0):
    return para(pid, text, para_pr=2, style=0, char_pr=char_pr)


def para_empty(pid):
    return (
        f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        f'<hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'
    )


def build_section0(items):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR,
    ]
    for i, item in enumerate(items, start=2):
        if item is None:
            parts.append(para_empty(i))
        elif isinstance(item, str):
            parts.append(para(i, item))
        else:
            fn, pid_ignored, *args = item
            parts.append(fn(i, *args))
    parts.append('</hs:sec>')
    return ''.join(parts)


# ── 문서 내용 정의 ──────────────────────────────────────────────

paragraphs = [
    # === 기안문 ===
    (para_title, 0, "기  안  문"),
    None,
    (para_subtitle, 0, "문서번호: 기획업무팀-2026-여름방학-001"),
    (para_subtitle, 0, "시행일자: 2026년 4월 14일"),
    (para_subtitle, 0, "기  안  자: 기획업무팀 기획담당"),
    (para_subtitle, 0, "결      재: 팀장 → 관장"),
    None,
    (para_subtitle, 0, "제목: 2026년 여름방학 어린이 평생학습 프로그램 운영 계획 승인 요청"),
    None,
    "1. 관련 근거",
    "  가. 「도서관법」 제28조 (공공도서관의 평생교육 기능)",
    "  나. 2026년 평생학습 운영 계획 (기획업무팀, 2026년 1월)",
    None,
    "2. 운영 목적",
    "  여름방학을 맞이하는 지역 어린이(5~10세)에게 창의·탐구 중심의 집중형 평생학습 프로그램을 제공하여, 도서관을 학습 및 문화의 공간으로 활용하고 독서 친밀도를 높이고자 합니다.",
    None,
    "3. 운영 개요",
    "  가. 기간: 2026년 7월 14일(화) ~ 8월 6일(목)",
    "  나. 프로그램 수: 2개 프로그램 동시 운영",
    "  다. 장소: 강의실 2호실, 강의실 3호실",
    "  라. 총 정원: 20명 (프로그램별 각 10명)",
    "  마. 총 소요 예산: 1,835,000원",
    "      - 강사료: 1,600,000원",
    "      - 재료비: 235,000원",
    None,
    "4. 프로그램 요약",
    "  가. 그림책 작가 도전! 나만의 그림책 만들기",
    "      - 대상: 5~7세 어린이 10명 / 강의실 2호실",
    "      - 일정: 매주 화·목, 오전 10:00~11:30, 총 8회",
    "      - 예산: 900,000원",
    None,
    "  나. 과학 탐정단: 여름 자연 실험실",
    "      - 대상: 8~10세 어린이 10명 / 강의실 3호실",
    "      - 일정: 매주 화·목, 오후 14:00~16:00, 총 8회",
    "      - 예산: 935,000원",
    None,
    "5. 향후 추진 일정",
    "  - 2026년 5월 11일: 강사 채용 공고 게시",
    "  - 2026년 6월 5일:  강사 선정 완료",
    "  - 2026년 6월 15일: 수강생 모집 공고 게시",
    "  - 2026년 6월 30일: 수강생 모집 마감",
    "  - 2026년 7월 14일: 프로그램 개강",
    None,
    "6. 붙임",
    "  붙임 1. 2026년 여름방학 어린이 평생학습 프로그램 운영 계획서 1부. 끝.",
    None,
    (para_center, 0, "기획업무팀 기획담당"),

    # === 구분선 / 첨부 시작 ===
    None,
    (para_center, 0, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"),
    None,
    (para_title, 0, "붙임 1. 2026년 여름방학 어린이 평생학습 프로그램 운영 계획서"),
    (para_subtitle, 0, "작성일: 2026년 4월 14일  /  담당: 기획업무팀 기획담당"),
    None,

    # 1. 운영 목적
    (para_subtitle, 0, "1. 운영 목적 및 배경"),
    "  공공도서관의 평생교육 기능 강화 및 지역 어린이의 방학 중 창의·탐구 활동 지원을 위하여, 연령별 발달 특성에 맞는 집중형 어린이 평생학습 프로그램 2종을 동시 운영한다.",
    None,

    # 2. 프로그램별 운영 계획
    (para_subtitle, 0, "2. 프로그램별 운영 계획"),
    None,

    # 프로그램 1
    (para_subtitle, 0, "[프로그램 1] 그림책 작가 도전! 나만의 그림책 만들기"),
    None,
    "  대상: 5~7세 어린이 (유아~초등 1학년)",
    "  정원: 10명",
    "  장소: 강의실 2호실",
    "  기간: 2026년 7월 14일(화) ~ 8월 6일(목)",
    "  일정: 매주 화요일·목요일, 오전 10:00~11:30 (90분/회, 총 8회)",
    "  목표: 그림책 읽기와 창작 활동을 통한 언어 표현력·상상력·시각 서사 능력 향상",
    None,
    "  [회차별 커리큘럼]",
    "  1회 / 7월 14일(화) / 그림책 탐험대 출발 — 그림책 감상, 이야기 씨앗 찾기",
    "  2회 / 7월 16일(목) / 주인공 만들기 — 캐릭터 설정 및 드로잉",
    "  3회 / 7월 21일(화) / 이야기의 배경 — 장소 상상, 배경 스케치",
    "  4회 / 7월 23일(목) / 스토리보드 — 기승전결 6컷 초안 작성",
    "  5회 / 7월 28일(화) / 그림 이야기 1 — 앞부분(1~3장면) 채색·글쓰기",
    "  6회 / 7월 30일(목) / 그림 이야기 2 — 중·뒷부분(4~6장면) 채색·글쓰기",
    "  7회 / 8월 4일(화)  / 표지 디자인 — 표지·제목·앞뒷면 완성",
    "  8회 / 8월 6일(목)  / 작가 발표회 — 제본, 낭독 발표, 수료식",
    None,
    "  [강사 자격요건]",
    "  - 아동미술지도사, 독서지도사, 유아교육 전공 등 관련 자격 소지자",
    "  - 공공도서관·문화센터 어린이 강의 경력 1년 이상 우대",
    None,
    "  [예산 명세]",
    "  - 강사료: 100,000원 × 8회 = 800,000원",
    "  - 재료비(그림책 제작 키트): 8,000원 × 10명 = 80,000원",
    "  - 재료비(제본 재료): 2,000원 × 10명 = 20,000원",
    "  - 소계: 900,000원",
    None,

    # 프로그램 2
    (para_subtitle, 0, "[프로그램 2] 과학 탐정단: 여름 자연 실험실"),
    None,
    "  대상: 8~10세 어린이 (초등 2~4학년)",
    "  정원: 10명",
    "  장소: 강의실 3호실 (일부 회차 도서관 야외 공간 활용)",
    "  기간: 2026년 7월 14일(화) ~ 8월 6일(목)",
    "  일정: 매주 화요일·목요일, 오후 14:00~16:00 (120분/회, 총 8회)",
    "  목표: 여름 자연 현상 탐구 실험과 독서 연계를 통한 과학적 사고력·관찰력·기록 능력 함양",
    None,
    "  [회차별 커리큘럼]",
    "  1회 / 7월 14일(화) / 탐정단 입단 — 오리엔테이션, 탐정 수첩 제작",
    "  2회 / 7월 16일(목) / 물의 비밀 — 표면장력·수압 실험, 결과 기록",
    "  3회 / 7월 21일(화) / 여름 식물 탐정 — 야외 채집·루페 관찰, 스케치",
    "  4회 / 7월 23일(목) / 빛과 그림자 — 굴절 실험, 프리즘 무지개 만들기",
    "  5회 / 7월 28일(화) / 날씨 탐정 — 구름 생성 실험, 날씨 관련 도서 탐독",
    "  6회 / 7월 30일(목) / 생태계 먹이사슬 — 카드게임, 생태 포스터 제작",
    "  7회 / 8월 4일(화)  / 나만의 발명품 — 물리 원리 활용 미니 발명품 제작",
    "  8회 / 8월 6일(목)  / 발표회 — 탐정 수첩 발표, 발명품 시연, 수료식",
    None,
    "  [강사 자격요건]",
    "  - 초등 과학·이공계 전공자로 아동 교육 경험 보유자",
    "  - 과학교육사, 자연생태해설사, 초등교원 자격 소지자 우대",
    "  - 도서관·과학관 등 공공기관 어린이 강의 경력 1년 이상 우대",
    None,
    "  [예산 명세]",
    "  - 강사료: 100,000원 × 8회 = 800,000원",
    "  - 재료비(탐정 수첩): 3,000원 × 10명 = 30,000원",
    "  - 재료비(실험 재료 세트): 7,000원 × 10명 = 70,000원",
    "  - 재료비(발명품 재료): 3,000원 × 10명 = 30,000원",
    "  - 수료 배지: 500원 × 10명 = 5,000원",
    "  - 소계: 935,000원",
    None,

    # 3. 일정
    (para_subtitle, 0, "3. 강사 채용 및 수강생 모집 일정"),
    None,
    "  [강사 채용]",
    "  - 채용 공고 게시: 2026년 5월 11일(월)",
    "  - 서류 접수 마감: 2026년 5월 29일(금)",
    "  - 심사 및 선정: 2026년 6월 1일 ~ 6월 5일",
    "  - 선정 통보: 2026년 6월 8일(월)",
    None,
    "  [수강생 모집]",
    "  - 모집 공고 게시: 2026년 6월 15일(월)",
    "  - 신청 접수 기간: 2026년 6월 15일 ~ 6월 30일 (선착순)",
    "  - 신청 방법: 도서관 홈페이지 온라인 접수 또는 방문 접수",
    "  - 대기자 등록: 각 프로그램 5명",
    None,

    # 4. 수료 기준
    (para_subtitle, 0, "4. 수료 기준"),
    "  - 전체 8회 중 6회(75%) 이상 출석 시 수료 인정",
    "  - 수료자에게 수료증 발급",
    None,

    # 5. 예산 종합
    (para_subtitle, 0, "5. 예산 종합"),
    None,
    "  프로그램 1 (그림책 만들기): 강사료 800,000원 + 재료비 100,000원 = 900,000원",
    "  프로그램 2 (과학 탐정단):  강사료 800,000원 + 재료비 135,000원 = 935,000원",
    "  합계:                      강사료 1,600,000원 + 재료비 235,000원 = 1,835,000원",
    None,
    "  ※ 2026년 평생학습 강사료 연간 예산 15,000,000원 중 1,600,000원 집행 (잔액 13,400,000원)",
    "  ※ 2026년 평생학습 재료비 연간 예산 3,000,000원 중 235,000원 집행 (잔액 2,765,000원)",
    None,
    (para_center, 0, "기획업무팀 기획담당"),
]


# ── 빌드 및 저장 ────────────────────────────────────────────────

def build_items(raw_items):
    """튜플 형태 항목을 문자열 xml 문단으로 변환"""
    result = []
    for item in raw_items:
        result.append(item)
    return result


def build_section0_from_list(raw_items):
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
        f'<hs:sec {FULL_NS}>',
        SECPR,
    ]
    pid = 2
    for item in raw_items:
        if item is None:
            parts.append(para_empty(pid))
        elif isinstance(item, str):
            parts.append(para(pid, item))
        elif isinstance(item, tuple):
            fn = item[0]
            args = item[2:]  # item[1] is dummy pid placeholder
            parts.append(fn(pid, *args))
        pid += 1
    parts.append('</hs:sec>')
    return ''.join(parts)


section0 = build_section0_from_list(paragraphs)

with zipfile.ZipFile(TEMPLATE, 'r') as src, \
     zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as dst:
    for item in src.infolist():
        if item.filename == 'Contents/section0.xml':
            dst.writestr(item, section0.encode('utf-8'))
        else:
            dst.writestr(item, src.read(item.filename))

print(f"생성 완료: {OUTPUT}")
