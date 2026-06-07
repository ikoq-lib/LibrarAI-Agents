# 도서목록 주제어 도우미 v4

ISBN 파일을 업로드하면 알라딘 Open API로 도서정보를 조회하고, 공공데이터포털 「문화체육관광부 국립중앙도서관_주제 정보 제공 서비스」를 함께 호출해 주제어 후보를 붙여 엑셀로 저장하는 Streamlit 서비스입니다.

## v4 수정 사항

- 기본 주제정보 API URL을 그대로 사용해도 테스트가 가능하도록 검증 오류를 수정했습니다.
- 주제정보 API 기본 설정값은 다음과 같습니다.
  - 호출 URL: `https://apis.data.go.kr/1371029/SubjectInformationService/getSubjectList`
  - 검색어 요청변수명: `label`
  - 페이지 요청변수명: `pageNo`
  - 건수 요청변수명: `numOfRows`
  - 응답형식 요청변수명: `type`
  - 응답형식 값: `json`

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
streamlit run app.py
```

## 사용 순서

1. 왼쪽 사이드바에 알라딘 TTBKey와 공공데이터포털 인증키를 입력합니다.
2. 공공데이터포털 키 형식은 우선 `일반 인증키(Decoding)`으로 테스트합니다.
3. 주제정보 API 설정은 기본값을 그대로 둡니다.
4. `주제정보 API 단독 테스트`에서 `환경`으로 먼저 테스트합니다.
5. ISBN 파일을 업로드하고 `도서목록 주제어 생성`을 누릅니다.

## 입력 파일

- `.txt`, `.csv`: 한 줄에 ISBN 하나씩 또는 쉼표/공백 구분
- `.xlsx`: ISBN이라는 이름이 포함된 열을 우선 사용, 없으면 첫 번째 열 사용
