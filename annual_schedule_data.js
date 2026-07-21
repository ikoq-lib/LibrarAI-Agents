// 자동 생성 파일 — scripts/gen_annual_schedule_data.py 실행으로 갱신. 직접 수정 금지.
// 소스: References/연간 업무 내역.xlsx(업무일정 시트) + References/업무_에이전트_매핑.md
const ANNUAL_SCHEDULE_ROWS = [
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "해당월 전월 1일~10일",
  "detail": "정기 수서 목록 작성."
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "정기 수서 목록 작성 후",
  "detail": "도서관 소장 도서와 비교하여 복본 조사"
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "복본 조사 후",
  "detail": "자료심의위원회를 개최하여 작성된 정기 수서 목록을 피드백 받기"
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "자료심의위원회 후",
  "detail": "수정한 정기 수서 목록으로 도서 구입 품의"
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "구입 도서 도착시",
  "detail": "구입 도서 검수 및 복본 조사"
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "구입 도서 검수 후",
  "detail": "KORMARC에 의거한 도서 MARC 작성"
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "구입 도서 MARC 작성 후",
  "detail": "장비작업, 도서 태깅 작업"
 },
 {
  "taskType": "자료개발",
  "taskName": "정기도서수서",
  "cycle": "2월, 5월, 8월, 11월. 분기별 1회",
  "timing": "해당월 1일~5일",
  "detail": "정기도서 자료실 이관"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "매주 첫째날",
  "detail": "지난 주 희망도서 목록을 취합하고 담당자가 심사(구입 제외 조건 및 복본 조사)"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "도서 심사 후",
  "detail": "구입 제외 도서를 신청한 이용자에게 제외 사유 알림(문자)"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "이용자에게 제외 사유 알림 후",
  "detail": "복본 조사"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "복본 조사 후",
  "detail": "도서 구입 품의 작성"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "구입 도서 도착시",
  "detail": "구입 도서 검수"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "구입 도서 검수 후",
  "detail": "KORMARC에 의거한 도서 MARC 작성"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "구입 도서 MARC 작성 후",
  "detail": "장비작업, 도서 태깅 작업"
 },
 {
  "taskType": "자료개발",
  "taskName": "희망도서수서",
  "cycle": "매주",
  "timing": "구입도서 장비 작업 후",
  "detail": "희망도서 자료실 이관"
 },
 {
  "taskType": "자료개발",
  "taskName": "수시도서수서",
  "cycle": "비정기",
  "timing": "수시 도서 요청시",
  "detail": "수시 수서 목록 작성"
 },
 {
  "taskType": "자료개발",
  "taskName": "수시도서수서",
  "cycle": "비정기",
  "timing": "수시 수서 목록 작성 후",
  "detail": "복본 조사"
 },
 {
  "taskType": "자료개발",
  "taskName": "수시도서수서",
  "cycle": "비정기",
  "timing": "복본 조사 후",
  "detail": "수시 도서 품의 작성 및 구입"
 },
 {
  "taskType": "자료개발",
  "taskName": "수시도서수서",
  "cycle": "비정기",
  "timing": "구입 도서 도착시",
  "detail": "구입 도서 검수"
 },
 {
  "taskType": "자료개발",
  "taskName": "수시도서수서",
  "cycle": "비정기",
  "timing": "구입 도서 검수 후",
  "detail": "KORMARC에 의거한 도서 MARC 작성"
 },
 {
  "taskType": "자료개발",
  "taskName": "수시도서수서",
  "cycle": "비정기",
  "timing": "구입 도서 MARC 작성 후",
  "detail": "장비작업, 도서 태깅 작업"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서점검",
  "cycle": "매년",
  "timing": "매년 5월 11일~15일",
  "detail": "장서점검 계획 수립(일정, 점검 범위 등, 매년 6월 1일~15일 사이로 계획)"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서점검",
  "cycle": "매년",
  "timing": "계획 수립된 장서점검 일정 당일",
  "detail": "도서 장서점검 실시(도서 존재여부, 훼손도서 여부 등)"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서점검",
  "cycle": "매년",
  "timing": "장서점검 후",
  "detail": "전산 데이터와 실존 데이터 매칭. 비매칭 자료는 실존 데이터 다시 탐색."
 },
 {
  "taskType": "자료개발",
  "taskName": "장서점검",
  "cycle": "매년",
  "timing": "장서 데이터 매칭 후",
  "detail": "결과보고서 작성(소재불명 자료, 장기연체자료, 훼손도서는 폐기)"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서점검",
  "cycle": "매년",
  "timing": "결과보고서 작성 후",
  "detail": "도서 폐기를 위한 폐기물 업체 선정 및 품의"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서점검",
  "cycle": "매년",
  "timing": "폐기물 업체 선정 및 품의 후",
  "detail": "폐기물 업체를 통한 폐기도서 폐기"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서현황보고",
  "cycle": "매월",
  "timing": "매월 1일~5일",
  "detail": "장서현황보고서 작성 및 보고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "매월 5일~10일",
  "detail": "다음달 독서진흥행사 주제 및 세부 내용 기획"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "독서진흥행사 기획 후",
  "detail": "상품 및 재료의 구입처와 예산 확인"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "독서진흥행사 기획 후",
  "detail": "강사가 필요할 경우 강사 섭외(강의료, 재료비 예산 확인 필수)"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "상품, 재료, 강사 내용 확인 후",
  "detail": "월별 독서진흥행사 계획 수립"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "월별 독서진흥행사 계획 수립 후",
  "detail": "범죄경력조회"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "매월 25일~30일",
  "detail": "다음달 독서진흥행사 세팅"
 },
 {
  "taskType": "독서진흥",
  "taskName": "월별 독서진흥행사",
  "cycle": "매월",
  "timing": "매월 1일~30일",
  "detail": "이번달 독서진흥행사 운영"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "매년 1월",
  "detail": "독서동아리 운영 계획 수립"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "각 독서동아리 운영 전",
  "detail": "독서동아리 신규 회원 모집"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "각 독서동아리 운영 전",
  "detail": "독서동아리 강사 모집 공고 작성"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 강사 모집 공고 후",
  "detail": "독서동아리 강사 모집 결과 보고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 강사 모집 결과 보고 후",
  "detail": "독서동아리 강사 선정 위원회"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 강사 선정 위원회 후",
  "detail": "독서동아리 강사 선정 결과 보고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 강사 선정 결과 보고 후 / 독서 동아리 강사 모집 결과 보고 후",
  "detail": "강사 범죄경력조회"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 강사 선정 결과 보고 후 / 독서 동아리 강사 모집 결과 보고 후",
  "detail": "독서동아리 강사 선정 공고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "강사 선정 공고 후",
  "detail": "강사 위촉"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 시작 전",
  "detail": "독서동아리 명단 보고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 운영일",
  "detail": "독서동아리 운영일지, 출석부 배부"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "독서동아리 운영일 다음날",
  "detail": "강사가 운영하는 독서동아리는 강사비 지급"
 },
 {
  "taskType": "독서진흥",
  "taskName": "독서동아리 운영",
  "cycle": "동아리별 상이",
  "timing": "매년 12월",
  "detail": "독서동아리 운영 결과보고"
 },
 {
  "taskType": "기획담당",
  "taskName": "주요업무계획수립",
  "cycle": "매년",
  "timing": "매년 1월 1일~10일",
  "detail": "도서관 각 업무 담당의 1년치 업무 계획을 취합하고 역점사업을 선정하여 주요업무계획작성"
 },
 {
  "taskType": "기획담당",
  "taskName": "월별통계작성",
  "cycle": "매월",
  "timing": "매월 1일~5일",
  "detail": "도서 대출, 행사 참여자, 평생학습 수강생 등 모든 수치를 취합하여 통계 보고서 작성 및 보고"
 },
 {
  "taskType": "자료개발",
  "taskName": "장서개발계획수립",
  "cycle": "매년",
  "timing": "매년 1월 1일~10일",
  "detail": "장서개발계획서 수립 및 보고"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "분기의 전월 1일~5일",
  "detail": "분기에 맞는 평생학습 강좌 기획 및 계획서 작성"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "평생학습 계획서 작성 후",
  "detail": "평생학습 강사 모집 공고 작성"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 모집 공고 후",
  "detail": "평생학습 강사 모집 결과 보고"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 모집 결과 보고 후",
  "detail": "평생학습 강사 선정 위원회"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 선정 위원회 후",
  "detail": "평생학습 강사 선정 결과 보고"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 선정 결과 보고 후",
  "detail": "강사 범죄경력조회"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 범죄경력조회 후",
  "detail": "평생학습 강사 선정 공고"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 선정 공고 후",
  "detail": "강사 위촉"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "강사 선정 공고 후(분기별 시작 최소 20일 전에 홍보물 게재 될 것)",
  "detail": "평생학습 수강생 모집"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "수강생 모집 후",
  "detail": "평생학습 수강생 모집 결과 보고"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "매 강의별",
  "detail": "평생학습 강좌별 운영일지, 출석부 배부"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "매월 말",
  "detail": "평생학습 강사비 지급"
 },
 {
  "taskType": "평생학습",
  "taskName": "평생학습강좌운영",
  "cycle": "매분기(1~2월(겨울방학), 3~6월(상반기), 7~8월(여름방학), 9~11월(하반기))",
  "timing": "분기별 평생학습 강좌 종료 후",
  "detail": "평생학습 운영 결과보고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "문화가있는날",
  "cycle": "매월",
  "timing": "매년 1월 15일~20일",
  "detail": "문화가 있는날 프로그램 기획 및 계획서 작성"
 },
 {
  "taskType": "독서진흥",
  "taskName": "문화가있는날",
  "cycle": "매월",
  "timing": "매월 마지막 수요일",
  "detail": "문화가 있는 날 프로그램 운영"
 },
 {
  "taskType": "독서진흥",
  "taskName": "문화가있는날",
  "cycle": "매월",
  "timing": "매년 1월 1일~5일",
  "detail": "전년도 문화가 있는 날 프로그램 결과 보고"
 },
 {
  "taskType": "독서진흥",
  "taskName": "북큐레이션",
  "cycle": "매월",
  "timing": "매년 1월 10일~20일",
  "detail": "올해 북큐레이션의 월별 주제와 도서 선정"
 },
 {
  "taskType": "독서진흥",
  "taskName": "북큐레이션",
  "cycle": "매월",
  "timing": "매월 1일",
  "detail": "그 달의 북큐레이션 홍보물 및 도서 비치"
 },
 {
  "taskType": "독서진흥",
  "taskName": "북큐레이션",
  "cycle": "매월",
  "timing": "매월 20일",
  "detail": "다음 달의 북큐레이션 홍보물 제작 및 도서 확보"
 },
 {
  "taskType": "독서진흥",
  "taskName": "북큐레이션",
  "cycle": "매월",
  "timing": "매년 12월 10일~20일",
  "detail": "올해 북큐레이션의 결과보고 작성"
 },
 {
  "taskType": "독서진흥",
  "taskName": "도서관 홍보",
  "cycle": "매월",
  "timing": "매년 1월 10일~20일",
  "detail": "올해 도서관 홍보 계획 수립"
 },
 {
  "taskType": "독서진흥",
  "taskName": "도서관 홍보",
  "cycle": "매월",
  "timing": "매월 15일~20일",
  "detail": "월별 독서진흥행사 계획 바탕으로 다음달 도서관 소식지 제작"
 },
 {
  "taskType": "독서진흥",
  "taskName": "도서관 홍보",
  "cycle": "매월",
  "timing": "매월 20일~25일",
  "detail": "도서관 소식지 실물 배포 및 온라인 게시"
 },
 {
  "taskType": "독서진흥",
  "taskName": "도서관 홍보",
  "cycle": "매월",
  "timing": "매월 20일~25일",
  "detail": "월별 독서진흥행사 계획 바탕으로 SNS 홍보 자료 제작 및 게시"
 },
 {
  "taskType": "독서진흥",
  "taskName": "도서관 홍보",
  "cycle": "매월",
  "timing": "매월 20일~25일",
  "detail": "월별 독서진흥행사 계획 바탕으로 보도자료 작성 및 게시"
 },
 {
  "taskType": "독서진흥",
  "taskName": "도서관 홍보",
  "cycle": "매월",
  "timing": "매월 20일~25일",
  "detail": "월별 독서진흥행사 계획 바탕으로 보도자료 작성 및 게시"
 },
 {
  "taskType": "기획담당",
  "taskName": "성과지표",
  "cycle": "매년",
  "timing": "매년 3월 10일~20일",
  "detail": "올해 도서관 성과지표 제출"
 },
 {
  "taskType": "기획담당",
  "taskName": "인문학",
  "cycle": "비정기",
  "timing": "매년 1월 10일~25일",
  "detail": "인문학 프로그램 강좌 기획 및 강사 섭외. 별도 공고는 필요하지 않음. 개별 섭외"
 },
 {
  "taskType": "기획담당",
  "taskName": "인문학",
  "cycle": "비정기",
  "timing": "매년 1월 25일~30일",
  "detail": "인문학 프로그램 운영 계획 수립"
 },
 {
  "taskType": "기획담당",
  "taskName": "도서관발전종합계획",
  "cycle": "매년",
  "timing": "매년 1월 20일~30일",
  "detail": "제O차 도서관발전종합계획에 따른 전년도 추진실적 보고"
 },
 {
  "taskType": "기획담당",
  "taskName": "독서문화진흥시행계획",
  "cycle": "매년",
  "timing": "매년 2월 10일~20일",
  "detail": "올해 독서문화진흥시행계획 수립 및 전년도 추진 실적 보고"
 },
 {
  "taskType": "기획담당",
  "taskName": "도서관가는길",
  "cycle": "매년",
  "timing": "매년 3월 10일~20일",
  "detail": "도서관 가는 길'에 실을 행사, 강연 등 내용 취합해서 작성 및 제출"
 },
 {
  "taskType": "기획담당",
  "taskName": "도서관의날",
  "cycle": "매년",
  "timing": "매년 3월 10일~20일",
  "detail": "도서관의 날 프로그램 운영 계획 수립"
 },
 {
  "taskType": "기획담당",
  "taskName": "도서관의날",
  "cycle": "매년",
  "timing": "매년 4월 3주차",
  "detail": "도서관의 날 프로그램 운영 계획에 따른 행사 운영"
 },
 {
  "taskType": "기획담당",
  "taskName": "도서관의날",
  "cycle": "매년",
  "timing": "매년 5월 1일~10일",
  "detail": "도서관의 날 프로그램 운영 결과 보고"
 },
 {
  "taskType": "기획담당",
  "taskName": "성과지표",
  "cycle": "매년",
  "timing": "매년 12월 10일~20일",
  "detail": "올해 도서관 성과지표 달성도 제출"
 }
];
const TASK_AGENT_MAP = {
 "정기도서수서": {
  "owners": [
   "dm01-collection-domain"
  ],
  "leafHint": "B-01",
  "note": "자료심의위원회 단계 포함 — 최종 조정은 escalation으로 chief-coordinator에 보고"
 },
 "희망도서수서": {
  "owners": [
   "dm01-collection-domain"
  ],
  "leafHint": "B-02, B-03",
  "note": "주간 계획서의 핵심 소스 — 매주 발생"
 },
 "수시도서수서": {
  "owners": [
   "dm01-collection-domain"
  ],
  "leafHint": "B-01, B-03",
  "note": "FN-01 미지정 업무 라우팅 경로로도 유입 가능"
 },
 "장서점검": {
  "owners": [
   "dm01-collection-domain"
  ],
  "leafHint": "B-06",
  "note": "폐기물 업체 선정 등 대외 계약 단계는 escalation"
 },
 "장서현황보고": {
  "owners": [
   "dm01-collection-domain"
  ],
  "leafHint": null,
  "note": "월별통계작성(기획담당)과 별개 — 장서 구성 현황 전용"
 },
 "장서개발계획수립": {
  "owners": [
   "dm01-collection-domain"
  ],
  "leafHint": null,
  "note": "연간 계획, 주요업무계획수립(기획담당)의 입력 자료"
 },
 "월별 독서진흥행사": {
  "owners": [
   "dm03-reading-culture-domain"
  ],
  "leafHint": "D-01/D-02/D-03",
  "note": "강사 필요 시 범죄경력조회 단계 포함"
 },
 "독서동아리 운영": {
  "owners": [
   "dm03-reading-culture-domain"
  ],
  "leafHint": "D-01, D-03",
  "note": "강사 2명 이상 지원 시 선정위원회 HITL — escalation"
 },
 "문화가있는날": {
  "owners": [
   "dm03-reading-culture-domain"
  ],
  "leafHint": null,
  "note": null
 },
 "북큐레이션": {
  "owners": [
   "dm03-reading-culture-domain",
   "dm01-collection-domain"
  ],
  "leafHint": "참고: DM-01 B-05 균형",
  "note": "도서 선정은 D3 event 성격, 장서 밸런스 참고 시 B-05"
 },
 "도서관 홍보": {
  "owners": [
   "dm05-pr-partnership-domain"
  ],
  "leafHint": "F-01 홍보물, F-04 소식지",
  "note": "독서진흥행사 계획(DM-03)이 원자료 — 실제 산출물은 D5 리프 업무"
 },
 "주요업무계획수립": {
  "owners": [
   "chief"
  ],
  "leafHint": null,
  "note": "전 도메인 계획 취합 — FN-02/A-01"
 },
 "월별통계작성": {
  "owners": [
   "chief"
  ],
  "leafHint": null,
  "note": "FN-03, A-02 경유 표준 통계 채널 그대로 사용"
 },
 "성과지표": {
  "owners": [
   "chief"
  ],
  "leafHint": "A-04 호출",
  "note": "상급기관 제출용"
 },
 "인문학": {
  "owners": [
   "dm04-lifelong-learning-domain"
  ],
  "leafHint": "계획 취합은 기획담당",
  "note": "분류는 기획담당이나 실제 운영은 평생학습 강좌 파이프라인과 동일"
 },
 "도서관발전종합계획": {
  "owners": [
   "chief"
  ],
  "leafHint": null,
  "note": "전 도메인 실적 취합, A-01"
 },
 "독서문화진흥시행계획": {
  "owners": [
   "dm03-reading-culture-domain",
   "chief"
  ],
  "leafHint": null,
  "note": "법정 계획 — 독서문화 실적이 근거자료"
 },
 "도서관가는길": {
  "owners": [
   "dm05-pr-partnership-domain",
   "chief"
  ],
  "leafHint": "F-04 유사",
  "note": "경남대표도서관 공문 연동, 대외 제출은 기획담당"
 },
 "도서관의날": {
  "owners": [
   "dm03-reading-culture-domain",
   "dm05-pr-partnership-domain",
   "chief"
  ],
  "leafHint": "행사 운영",
  "note": "복수 도메인 — chief-coordinator가 편집·통합"
 },
 "평생학습강좌운영": {
  "owners": [
   "dm04-lifelong-learning-domain"
  ],
  "leafHint": "E-01~E-04",
  "note": "강사 2명 이상 지원 시 선정위원회 HITL — escalation"
 }
};
