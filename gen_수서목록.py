# -*- coding: utf-8 -*-
import zipfile, xml.sax.saxutils as X

TMPL = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUT  = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_1-2월_신간도서_구입목록.hwpx"

NS = ('xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
      'xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
      'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
      'xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" '
      'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" xmlns:dc="http://purl.org/dc/elements/1.1/" '
      'xmlns:opf="http://www.idpf.org/2007/opf/" xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" '
      'xmlns:epub="http://www.idpf.org/2007/ops" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"')

SECPR = '<hp:p id="1" paraPrIDRef="29" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="0"><hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" outlineShapeIDRef="1" memoShapeIDRef="1" textVerticalWidthHead="0" masterPageCnt="0"><hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/><hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/><hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/><hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/><hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY"><hp:margin header="4251" footer="4251" gutter="0" left="5669" right="5669" top="4251" bottom="4251"/></hp:pagePr><hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr><hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr><hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill></hp:secPr><hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl></hp:run></hp:p>'

def para(pid, t, pp=7, s=0, cp=5):
    return f'<hp:p id="{pid}" paraPrIDRef="{pp}" styleIDRef="{s}" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="{cp}"><hp:t>{X.escape(t)}</hp:t></hp:run></hp:p>'

def emp(pid):
    return f'<hp:p id="{pid}" paraPrIDRef="7" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0"><hp:run charPrIDRef="5"><hp:t/></hp:run></hp:p>'

# (순번, KDC, 서명, 저자, 출판사, 출판월, 정가, 수량, 합계)
BOOKS = [
    ( 1,'004.3','AI 시대의 정보 리터러시',       '김정훈',   '한국출판사',     '2026.01',18000,1,18000),
    ( 2,'020.1','디지털 아카이브와 미래 도서관',  '이수민',   '문헌정보사',     '2026.02',22000,1,22000),
    ( 3,'101',  '존재와 의미: 현대인의 철학',     '박철수',   '철학과현실사',   '2026.01',16000,1,16000),
    ( 4,'188',  '윤리적 AI를 생각한다',           '최지은',   '사이언스북스',   '2026.02',20000,1,20000),
    ( 5,'189',  '인공지능 시대의 인문학',          '최재천',   '김영사',         '2026.01',22000,1,22000),
    ( 6,'224',  '명상과 마음챙김의 과학',          '정민아',   '불광출판사',     '2026.01',17000,1,17000),
    ( 7,'302',  '2026년 한국 사회 트렌드',         '김난도 외','미래의창',       '2026.01',19800,3,59400),
    ( 8,'320',  '디지털 민주주의의 도전',          '정희수',   '후마니타스',     '2026.01',20000,1,20000),
    ( 9,'325',  '디지털 전환 시대의 경영 전략',    '송기창',   '박영사',         '2026.02',28000,1,28000),
    (10,'331',  '인구 감소 시대의 지역 소멸',      '강성훈',   '돌베개',         '2026.01',18000,1,18000),
    (11,'334',  '고령화 사회와 노인 문제',          '정경희',   '나남',           '2026.02',24000,1,24000),
    (12,'339',  '기후 정책과 탄소중립 사회',        '이재현',   '한울아카데미',   '2026.02',25000,1,25000),
    (13,'401',  '기후과학 입문',                   '박성진',   '사이언스북스',   '2026.01',22000,1,22000),
    (14,'440',  '우주의 비밀: 천문학 입문',        '이명현',   '사이언스북스',   '2026.02',25000,1,25000),
    (15,'471',  '뇌과학이 알려주는 행복의 비밀',   '이민경',   '동아시아',       '2026.01',18000,1,18000),
    (16,'511',  '생성형 AI 실무 활용법',           '김태연',   '한빛미디어',     '2026.01',28000,3,84000),
    (17,'513',  '건강 수명 100세 프로젝트',        '장수영',   '중앙북스',       '2026.01',17000,2,34000),
    (18,'517',  '스마트팜 혁명과 미래 농업',        '최병호',   '농민신문사',     '2026.02',23000,1,23000),
    (19,'594',  '음식의 과학과 건강',               '정재훈',   '한국경제신문사', '2026.02',19000,1,19000),
    (20,'600',  'K-컬처의 세계화',                 '윤진아',   '아트북스',       '2026.01',19000,1,19000),
    (21,'609',  '현대 도예의 흐름',                 '이선화',   '미진사',         '2026.02',32000,1,32000),
    (22,'679',  '국악의 역사와 현재',               '박성희',   '민속원',         '2026.01',28000,1,28000),
    (23,'710',  '한국어의 미래',                    '남길임',   '역락',           '2026.01',16000,1,16000),
    (24,'811',  '불안의 시대를 걷다 (시집)',         '황인찬',   '문학과지성사',   '2026.01',13000,1,13000),
    (25,'813',  '봄의 끝자락에서',                  '정세랑',   '문학동네',       '2026.01',16800,3,50400),
    (26,'813',  '우리가 남긴 것들',                  '최은영',   '민음사',         '2026.01',14500,3,43500),
    (27,'813',  '기억의 방',                        '이현',     '창비',           '2026.02',15000,1,15000),
    (28,'813',  '그 겨울의 끝에서',                  '박상영',   '한겨레출판',     '2026.02',15500,1,15500),
    (29,'911',  '한반도 근현대사 100년',             '박찬승',   '돌베개',         '2026.02',25000,1,25000),
    (30,'911',  '조선 후기 경제사 재해석',           '이영훈',   '일조각',         '2026.01',28000,1,28000),
]

total_qty   = sum(b[7] for b in BOOKS)
total_amt   = sum(b[8] for b in BOOKS)

rows = []
rows.append(('2026년 1~2월 신간 도서 구입 목록', 2, 0, 2))
rows.append(None)
rows.append(('■ 구입 기간: 2026. 5. 15. ~ 2026. 5. 30.  |  구입 규모: 30종 38권  |  소요금액: 금799,800원', 3, 0, 1))
rows.append(None)

# 표 헤더
HDR = f"{'순':>3}  {'KDC':<6}  {'서명':<22}  {'저자':<8}  {'출판사':<10}  {'출판월':<8}  {'정가':>8}  {'수량':>3}  {'금액':>9}"
DIV = '─' * len(HDR)
rows.append((HDR, 7, 0, 1))
rows.append((DIV, 7, 0, 1))

for b in BOOKS:
    no, kdc, title, author, pub, month, price, qty, amt = b
    line = f"{no:>3}  {kdc:<6}  {title:<22}  {author:<8}  {pub:<10}  {month:<8}  {price:>8,}  {qty:>3}  {amt:>9,}"
    rows.append((line, 7, 0, 5))

rows.append((DIV, 7, 0, 1))
rows.append((f"{'합  계':<45}  {'':>8}  {total_qty:>3}  {total_amt:>9,}", 7, 0, 5))
rows.append(None)

# KDC 분류별 요약
from collections import defaultdict
kdc_sum = defaultdict(lambda: [0, 0])
kdc_name = {'0':'총류', '1':'철학', '2':'종교', '3':'사회과학', '4':'자연과학',
            '5':'기술과학', '6':'예술', '7':'언어', '8':'문학', '9':'역사'}
for b in BOOKS:
    k = b[1][0]
    kdc_sum[k][0] += b[7]
    kdc_sum[k][1] += b[8]

rows.append(('■ KDC 분류별 현황', 3, 0, 3))
rows.append(None)
rows.append((f"{'분류':<12}  {'종수':>5}  {'권수':>5}  {'금액':>10}", 7, 0, 1))
rows.append(('─' * 38, 7, 0, 1))

title_cnt = defaultdict(int)
for b in BOOKS:
    title_cnt[b[1][0]] += 1

for k in sorted(kdc_sum.keys()):
    name = kdc_name.get(k, k)
    tc = title_cnt[k]
    qc, ac = kdc_sum[k]
    rows.append((f"{k+'00 '+name:<12}  {tc:>5}종  {qc:>5}권  {ac:>10,}원", 7, 0, 5))

rows.append(('─' * 38, 7, 0, 1))
rows.append((f"{'합  계':<12}  {30:>5}종  {total_qty:>5}권  {total_amt:>10,}원", 7, 0, 5))

parts = [f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>', f'<hs:sec {NS}>', SECPR]
for i, r in enumerate(rows, 2):
    parts.append(emp(i) if r is None else para(i, r[0], r[1], r[2], r[3]))
parts.append('</hs:sec>')
sec0 = ''.join(parts)

with zipfile.ZipFile(TMPL, 'r') as s, zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as d:
    for item in s.infolist():
        d.writestr(item, sec0.encode('utf-8') if item.filename == 'Contents/section0.xml' else s.read(item.filename))
print('목록 생성:', OUT)
print(f'총 {len(BOOKS)}종 {total_qty}권 / {total_amt:,}원')
