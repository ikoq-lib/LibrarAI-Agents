# B-01 주간 추천도서 후보 풀 전환 (2026-07-26)

## 배경

- 요청 때마다 장르별 웹 그라운딩을 실행하는 방식은 1회 약 90초가 걸리고 현실적으로 40~55종 수준이라, 정기수서에서 필요한 수백 종을 안정적으로 처리할 수 없었다.
- SEOJI 전체 신간에는 학술·정부·자가출판 자료가 많이 섞이고 소프트 쿼터가 있어 발굴원으로 부적합했다.

## 확정 구조

1. 8개 고정 출처를 주 1회 취합한다: 출판유통통합전산망 20, 교보문고 15, YES24 15, 한겨레 5, 동아일보 5, 국립중앙도서관 5, 국립어린이청소년도서관 5, 도서관 정보나루 5.
2. 인플루언서·북튜버는 토큰 대비 효율 문제로 제외한다. 한겨레와 동아일보는 각각 5종의 동일 상한으로 언론 성향 균형을 유지한다.
3. 직접 HTML/PDF 수집을 우선하고, 직접 수집이 막히거나 할당량이 부족한 출처만 도메인 제한 AI 웹 검색으로 보완한다. 1차 병합 후 40종 미만일 때만 알라딘·영풍문고를 예비 출처로 사용한다.
4. 별도 테이블 `public.acquisition_candidates`에 후보를 누적한다. 전체 소장 장서 `public.books`와 분리한다.
5. ISBN 우선, ISBN이 없으면 정규화한 제목+저자로 중복 병합한다.
6. 추천 출처는 `sources[]`, 독립 출처 수는 `recommend_count`로 누적해 사회적 관심도 신호로 사용한다.
7. SEOJI는 취합 후보의 실존·서지·포맷을 베스트에포트 검증한다. 미등록·무응답 후보는 `verified=false`로 보존하고 발주 전 사서 재확인을 요구한다.
8. 원시 후보 65~75종, 최종 저장 40~50종을 목표로 한다. 40종 이상은 정상 성공, 30~39종은 부분 성공 경고, 30종 미만은 실패다.
9. B-01 요청 시 후보 풀을 먼저 조회한다. 조회 장애나 빈 결과일 때만 기존 실시간 발굴을 예비 경로로 사용한다.
10. 구매 확정 전까지 후보는 `acquisition_candidates`에 남고, 확정 후에만 `public.books`로 승격한다.

## 구현 파일

- `db/acquisition_candidates.sql`
- `scripts/harvest-acquisition-candidates.mjs`
- `.github/workflows/harvest-acquisition-candidates.yml`
- `api/acquisition-candidates.js`
- `LibrarAI.html`의 B-01 캐시 우선 조회 경로

## 운영 주기

- GitHub Actions: 매주 월요일 03:00(Asia/Seoul)
- 수동 실행: `workflow_dispatch`
- 필요한 저장소 비밀값: `OPENROUTER_API_KEY`, `SEOJI_API_KEY_NL_DIRECT`, `SUPABASE_DB_PASSWORD`

## 아직 남은 작업

- 수백 종의 점수·예산 배분·Excel 행은 LLM이 직접 쓰지 않고 시스템 코드가 결정론적으로 생성하도록 분리해야 한다.
- 구매 확정 시 `acquisition_candidates.status='purchased'` 변경과 `public.books` 승격은 사서 승인 뒤 실행하는 별도 작업으로 구현해야 한다.
- 원격 Supabase 연결 인증을 복구한 뒤 `books`와 `acquisition_candidates` 실조회 및 첫 취합 적재를 검증해야 한다.
