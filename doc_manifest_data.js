// 문서 매니페스트 — 월간계획 확정본에서 만들 실행 문서 목록의 근거 데이터.
// 설계: PRD/월간계획_확정_문서번들_설계.md 5절 (2026-09-03 사서 확정 · 4단계 구현)
//
// taskName 은 annual_schedule_data.js 의 taskName 과 정확히 일치해야 한다.
// 정합성 검사: python scripts/check_doc_manifest.py
//
// repeat   monthly | weekly | quarterly:[..] | yearly:[..] | conditional | manual
// leaf     LibrarAI.html DOMAINS[].agents[].id. null 이면 chief 직접 생성
// tpl      A-01 카탈로그 번호. null 이면 등록 양식 없음 → TPL-001 기본형 + "양식 미등록" 배지
// format   hwpx | xlsx | none(문서 산출물이 아님 — 목록에는 남기되 번들에서 제외)
// title    {m} 월 · {n} 차수(주차·분기)
const DOC_MANIFEST_ROWS = [
 {
  taskName: "정기도서수서", owner: "dm01-collection-domain", leaf: "b01-acquisition",
  repeat: "quarterly:[2,5,8,11]", condition: null,
  docs: [
   { tpl: "TPL-017", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{n}차 정기도서 구입 자료심의위원회 개최" },
   { tpl: "ATT-009", kind: "붙임", format: "xlsx", skeleton: null, title: "{n}차 정기구입 도서 심의대상 목록" },
   { tpl: "TPL-018", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{n}차 자료심의위원회 회의 결과" },
   { tpl: null, kind: "붙임", format: "hwpx", skeleton: null, title: "{n}차 자료심의위원회 회의록", note: "실물은 References/문서 샘플/자료개발에 있으나 번호 미등록" },
   { tpl: "TPL-019", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{n}차 정기도서 구입 건의" },
   { tpl: "ATT-010", kind: "붙임", format: "xlsx", skeleton: null, title: "{n}차 정기도서 구입 목록(심의 후 확정)" },
  ],
 },
 {
  taskName: "정기도서수서", owner: "dm01-collection-domain", leaf: "b01-acquisition",
  repeat: "conditional", condition: "위원회 미구성",
  docs: [
   { tpl: "TPL-016", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{n}차 자료심의위원회 구성" },
  ],
 },
 {
  taskName: "정기도서수서", owner: "dm01-collection-domain", leaf: "b01-acquisition",
  repeat: "conditional", condition: "웹툰도서 포함",
  docs: [
   { tpl: "TPL-020", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{n}차 웹툰도서 구입 건의", note: "결재선 예외 — 사서팀장·도서관장(주무관 없음)" },
   { tpl: "ATT-011", kind: "붙임", format: "xlsx", skeleton: null, title: "{n}차 웹툰도서 구입 목록" },
  ],
 },
 {
  taskName: "희망도서수서", owner: "dm01-collection-domain", leaf: "b02-wishlist",
  repeat: "monthly", condition: null,
  docs: [
   { tpl: "TPL-014", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m}월 희망도서 구입 건의" },
   { tpl: "ATT-007", kind: "붙임", format: "xlsx", skeleton: null, title: "{m}월 희망도서 구입 목록" },
  ],
 },
 {
  taskName: "수시도서수서", owner: "dm01-collection-domain", leaf: "b01-acquisition",
  repeat: "manual", condition: null,
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "수시도서 구입 건의" },
  ],
 },
 {
  taskName: "장서점검", owner: "dm01-collection-domain", leaf: "b06-inspection",
  repeat: "yearly:[5,6]", condition: null,
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m}월 장서점검 계획 수립" },
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m}월 장서점검 결과 보고" },
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "폐기 대상 자료 심의 품의" },
  ],
 },
 {
  taskName: "장서현황보고", owner: "dm01-collection-domain", leaf: "b05-balance",
  repeat: "monthly", condition: null,
  docs: [
   { tpl: "TPL-015", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m}월 장서현황 보고" },
   { tpl: "ATT-008", kind: "붙임", format: "xlsx", skeleton: null, title: "{m}월 장서현황(KDC 류별×자료실)" },
  ],
 },
 {
  taskName: "장서개발계획수립", owner: "dm01-collection-domain", leaf: "b01-acquisition",
  repeat: "yearly:[1]", condition: null,
  docs: [
   { tpl: "TPL-013", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{y}년 자료 확충 계획 수립" },
   { tpl: "ATT-006", kind: "붙임", format: "hwpx", skeleton: null, title: "{y}년 자료 확충 계획(연간정책·예산·통계·산출공식)" },
  ],
 },
 {
  taskName: "월별 독서진흥행사", owner: "dm03-reading-culture-domain", leaf: "planner",
  repeat: "monthly", condition: null,
  docs: [
   { tpl: "TPL-002", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m2}월 독서진흥행사 운영 계획", note: "문화가있는날·북큐레이션 내용을 이 문서에 함께 담는다" },
   { tpl: null, kind: "붙임", format: "hwpx", skeleton: null, title: "{m2}월 독서진흥행사 운영 계획 본문" },
   { tpl: "TPL-009", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m0}월 독서진흥행사 운영 결과" },
   { tpl: null, kind: "붙임", format: "hwpx", skeleton: null, title: "{m0}월 독서진흥행사 운영 결과 본문" },
  ],
 },
 {
  taskName: "월별 독서진흥행사", owner: "dm03-reading-culture-domain", leaf: "instructor-sourcing",
  repeat: "conditional", condition: "강사 있음",
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "강사 범죄경력조회 요청" },
  ],
 },
 {
  taskName: "독서동아리 운영", owner: "dm03-reading-culture-domain", leaf: "reading-club",
  repeat: "manual", condition: null, unitLabel: "동아리 수",
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "독서동아리 회원 모집 공고" },
   { tpl: "TPL-022", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "독서동아리 강사 모집 공고", note: "평생학습 TPL 준용" },
   { tpl: "TPL-025", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "독서동아리 강사 선정 결과 보고", note: "평생학습 TPL 준용" },
   { tpl: "TPL-029", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "독서동아리 강사 위촉", note: "평생학습 TPL 준용" },
   { tpl: null, kind: "붙임", format: "hwpx", skeleton: null, title: "독서동아리 운영일지·출석부" },
   { tpl: "TPL-027", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "독서동아리 강사비 지급", note: "평생학습 TPL 준용" },
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "독서동아리 운영 결과 보고" },
  ],
 },
 {
  taskName: "평생학습강좌운영", owner: "dm04-lifelong-learning-domain", leaf: "ll-planner",
  repeat: "quarterly:[1,4,7,10]", condition: null,
  docs: [
   { tpl: "TPL-021", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 프로그램 운영 계획 수립" },
   { tpl: "ATT-004", kind: "붙임", format: "hwpx", skeleton: null, title: "{half} 평생학습 프로그램 운영 계획(붙임 세트)" },
   { tpl: "TPL-022", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 강사 모집 공고" },
   { tpl: "ATT-001", kind: "붙임", format: "hwpx", skeleton: null, title: "강사 모집 공고문(지원서·강의계획서 포함)" },
   { tpl: "TPL-023", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 강사 모집 결과 보고" },
   { tpl: "TPL-024", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 강사 선정위원회 개최" },
   { tpl: "ATT-002", kind: "붙임", format: "hwpx", skeleton: null, title: "강사 선정 심사 기준표" },
   { tpl: "TPL-025", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 강사 선정 결과 보고" },
   { tpl: "TPL-012", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 강사 선정 결과 공고(게시 승인)" },
   { tpl: "ATT-012", kind: "붙임", format: "hwpx", skeleton: null, title: "강사 선정 결과 공고문(게시용)" },
   { tpl: "TPL-029", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 강사 위촉" },
   { tpl: "TPL-026", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 수강생 모집 결과 보고" },
   { tpl: "ATT-005", kind: "붙임", format: "xlsx", skeleton: null, title: "수강생 등록 명단" },
   { tpl: "TPL-028", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{half} 평생학습 프로그램 운영 결과 보고" },
   { tpl: "ATT-003", kind: "붙임", format: "hwpx", skeleton: null, title: "운영 결과 본문(설문조사 포함)" },
  ],
 },
 {
  taskName: "평생학습강좌운영", owner: "dm04-lifelong-learning-domain", leaf: "ll-operation-log",
  repeat: "monthly", condition: null,
  docs: [
   { tpl: "TPL-027", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m}월 평생학습 강사비 지급" },
   { tpl: "ATT-013", kind: "붙임", format: "xlsx", skeleton: null, title: "{m}월 평생학습 강사비 지급 내역" },
  ],
 },
 {
  taskName: "평생학습강좌운영", owner: "dm04-lifelong-learning-domain", leaf: "ll-operation-log",
  repeat: "manual", condition: null, unitLabel: "강좌 수",
  docs: [
   { tpl: null, kind: "붙임", format: "hwpx", skeleton: null, title: "평생학습 강좌 운영일지·출석부" },
  ],
 },
 {
  taskName: "문화가있는날", owner: "dm03-reading-culture-domain", leaf: "planner",
  repeat: "monthly", condition: null,
  docs: [],
  note: "별도 문서 없음 — 월별 독서진흥행사 운영계획·운영결과에 포함",
 },
 {
  taskName: "북큐레이션", owner: "dm03-reading-culture-domain", leaf: "planner",
  repeat: "monthly", condition: null,
  docs: [
   { tpl: null, kind: "홍보물 문구", format: "none", skeleton: null, title: "{m}월 북큐레이션 홍보 문구" },
  ],
  note: "기안문은 별도로 만들지 않는다 — 월별 독서진흥행사 문서에 포함",
 },
 {
  taskName: "도서관 홍보", owner: "dm05-pr-partnership-domain", leaf: "f04-newsletter",
  repeat: "monthly", condition: null,
  docs: [
   { tpl: "TPL-031", kind: "기안문", format: "hwpx", skeleton: "SK-대외발송", title: "소식지 「우포」 {m}월호(통권 제{issue}호) 배부", note: "유일한 대외 발송 공문 — 수신자 참조 + 발신명의" },
   { tpl: "ATT-015", kind: "붙임", format: "hwpx", skeleton: "SK-소식지원고", title: "소식지 {m}월호 본체 원고", note: "원고 텍스트만 생성 — 4쪽 디자인 편집은 사람이 입힌다" },
   { tpl: "TPL-030", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "[홍보_보도자료] {m}월 보도자료 배포", note: "소요금액·예산과목 항목 없음" },
   { tpl: "ATT-014", kind: "붙임", format: "hwpx", skeleton: "SK-보도자료", title: "{m}월 보도자료 본체" },
   { tpl: null, kind: "디자인", format: "none", skeleton: null, title: "홍보 안내문(A4 포스터)" },
   { tpl: null, kind: "SNS", format: "none", skeleton: null, title: "{m}월 SNS 게시 문구" },
  ],
 },
 {
  taskName: "월별통계작성", owner: "chief", leaf: null,
  repeat: "monthly", condition: null,
  docs: [
   { tpl: "TPL-032", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{m}월 도서관 이용 실적 보고" },
   { tpl: "ATT-016", kind: "붙임", format: "xlsx", skeleton: null, title: "{m}월 및 누적 이용실적 통계표" },
  ],
 },
 {
  taskName: "주요업무계획수립", owner: "chief", leaf: null,
  repeat: "yearly:[1]", condition: null,
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{y}년 주요업무계획 수립" },
  ],
 },
 {
  taskName: "성과지표", owner: "chief", leaf: "a04-performance-management",
  repeat: "yearly:[3,12]", condition: null,
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{y}년 성과지표 제출" },
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{y}년 성과지표 달성도 제출" },
  ],
 },
 {
  taskName: "인문학", owner: "dm04-lifelong-learning-domain", leaf: "ll-planner",
  repeat: "yearly:[1]", condition: null,
  docs: [
   { tpl: "TPL-021", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{y}년 인문학 프로그램 운영 계획 수립", note: "평생학습 TPL-021 준용" },
  ],
 },
 {
  taskName: "도서관발전종합계획", owner: "chief", leaf: null,
  repeat: "yearly:[1]", condition: null,
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "도서관발전종합계획 전년도 추진실적 보고" },
  ],
 },
 {
  taskName: "독서문화진흥시행계획", owner: "chief", leaf: "planner",
  repeat: "yearly:[2]", condition: null,
  docs: [
   { tpl: null, kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "{y}년 독서문화진흥 시행계획 및 전년 실적 보고" },
  ],
 },
 {
  taskName: "도서관가는길", owner: "dm05-pr-partnership-domain", leaf: "f04-newsletter",
  repeat: "yearly:[3]", condition: null,
  docs: [
   { tpl: null, kind: "원고", format: "hwpx", skeleton: null, title: "「도서관 가는 길」 원고 취합·제출" },
  ],
 },
 {
  taskName: "도서관의날", owner: "dm03-reading-culture-domain", leaf: "planner",
  repeat: "yearly:[3,4,5]", condition: null,
  docs: [
   { tpl: "TPL-002", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "도서관의 날 행사 운영 계획", note: "TPL-002 준용" },
   { tpl: "TPL-009", kind: "기안문", format: "hwpx", skeleton: "SK-기안문", title: "도서관의 날 행사 운영 결과", note: "TPL-009 준용" },
  ],
 },
];

// 문서 종류별 텍스트 골격 — 5단계(문서화 패스)에서 채운다.
// 설계 8절의 SK-기안문 / SK-대외발송 / SK-소식지원고 / SK-보도자료가 들어갈 자리다.
const DOC_SKELETONS = {};
