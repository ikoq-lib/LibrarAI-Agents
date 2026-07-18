---
name: project_db_schema_status
description: 장서 DB(Supabase project tkyaganfdfiuesvbcbkr)의 실제 스키마 현황과 FN-03 수행 시 제약
metadata:
  type: project
---

**2026-07-11 확인:** Supabase 프로젝트 `tkyaganfdfiuesvbcbkr`의 public 스키마에는 `public.books` 테이블 단 하나만 존재한다 (73,390행). 대출 이력(loan_history)·예약 큐(reservation) 테이블은 아직 없다.

- `books`는 **등록번호(reg_no) 단위 그레인** — 실물 1부 = 1행. 즉 동일 ISBN에 대해 여러 행이 있으면 그것이 복본 부수다. `dup_no` 컬럼이 복본 순번(2, 3...)을 나타내고 1번째 부수는 보통 null.
- 컬럼: reg_no, title, author, publisher, pub_year, loc_mark, call_no, vol, dup_no, room, shelf, material_status(이용가능/기타), loan_status(대출가능/대출중 등 **현재 상태만**, 이력 아님), is_blind, is_biblio_blind, ctrl_no, isbn, price, updated_at.
- ISBN 컬럼은 10자리(구 ISBN)와 13자리가 혼재되어 저장되어 있음 (예: "8949110091"과 "9788949111452"가 같은 시리즈의 다른 책에 각각 존재). ISBN 완전일치 조회 시 10/13자리 두 형태 모두 고려해야 할 수 있음.

**Why:** FN-03(추가 구입 필요성 분석)은 최근 3개월 대출 실적과 예약 대기 건수를 요구하는데, 현재 DB에는 이 이력 데이터가 전혀 없다. `loan_status`는 스냅샷(현재 대출중/가능 여부)일 뿐 3개월 집계가 불가능하다.

**How to apply:** 대출·예약 이력 테이블이 추가되기 전까지, FN-01에서 `duplicate` 확정된 모든 건에 대해 FN-03은 예외처리 규정대로 "복본 확정, 추가구입 필요성은 데이터 부족으로 판단 보류"로 응답한다. `existing_copies`는 동일 ISBN(10/13자리 모두 확인)의 행 수로 계산 가능하니 이것만 제공한다. 향후 loan_history/reservation 테이블이 생기면 이 메모를 갱신할 것.
