# -*- coding: utf-8 -*-
import zipfile, xml.sax.saxutils as X

TMPL = r"C:/Users/User/.claude/skills/hwpx-autofill-conversion/examples/(샘플양식1) 보고서 기본 양식.hwpx"
OUT  = r"C:/Users/User/Desktop/vibe_study/LibrarAI/2026년_1-2월_신간도서_구입계획_기안문.hwpx"

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

rows = [
    ('경상남도교육청 창녕도서관', 2, 0, 2),
    None,
    ('수신  내부결재', 3, 0, 1),
    ('(경유)', 3, 0, 1),
    ('제목  2026년 1~2월 신간 도서 구입 계획', 3, 0, 3),
    None,
    ('1. 관련: 문헌정보1담당-73(2026.1.6., 「2026년 주요업무계획 수립」)', 7, 0, 5),
    ('2. 2026년 1월~2월 출간 성인 신간 도서를 아래와 같이 구입하고자 합니다.', 7, 0, 5),
    None,
    ('  가. 구입기간: 2026. 5. 15. ~ 2026. 5. 30.', 7, 0, 5),
    ('  나. 구입대상: 성인 도서 (2026년 1~2월 출간 신간)', 7, 0, 5),
    ('  다. 구입규모: 30종 39권', 7, 0, 5),
    ('  라. 소요금액: 금799,800원(금칠십구만구천팔백원)', 7, 0, 5),
    ('  마. 예산과목: 자료구입비', 7, 0, 5),
    None,
    ('붙임  2026년 1~2월 신간 도서 구입 목록 1부.  끝.', 7, 0, 5),
    None, None, None,
    ('기안자  주무관               검토자  문헌정보1담당장               결재권자  도서관장', 7, 0, 5),
    None,
    ('시행  창녕도서관-XX(2026. 5. 2.)    접수 ( )', 3, 0, 1),
    ('우 50331 경상남도 창녕군 창녕읍 남창녕로 52 / http://cnlib.gne.go.kr / 전화 055-532-9506 / 전송 055-532-9507 / 공개', 3, 0, 1),
]

parts = [f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>', f'<hs:sec {NS}>', SECPR]
for i, r in enumerate(rows, 2):
    parts.append(emp(i) if r is None else para(i, r[0], r[1], r[2], r[3]))
parts.append('</hs:sec>')
sec0 = ''.join(parts)

with zipfile.ZipFile(TMPL, 'r') as s, zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as d:
    for item in s.infolist():
        d.writestr(item, sec0.encode('utf-8') if item.filename == 'Contents/section0.xml' else s.read(item.filename))
print('기안문 생성:', OUT)
