---
name: reference-supabase-schema
description: B-06이 사용하는 Supabase 프로젝트 ID와 관련 테이블(inspection_batches/inspection_scans/disposal_candidates/books) 실제 스키마
metadata:
  type: reference
---

B-06(장서점검) 관련 실제 데이터는 Supabase 프로젝트 `tkyaganfdfiuesvbcbkr`(ikoq-lib's Project, ap-southeast-1, ACTIVE_HEALTHY, 2026-07-11 생성)에 있다. 구 프로젝트 `jzoriabwegcnqxolzttq`는 INACTIVE 상태이므로 사용하지 않는다.

**관련 테이블(public 스키마):**
- `books` (73,390행, PK `reg_no`): 장서 원부. 등록번호 단위 그레인. 컬럼: reg_no, title, author, publisher, pub_year, loc_mark, call_no, vol, dup_no, room, shelf, `material_status`, `loan_status`, is_blind, is_biblio_blind, ctrl_no, isbn, price, updated_at. 결본 확정 시 `material_status`를 갱신하는 대상 테이블(예: '소재불명').
- `inspection_batches` (PK `batch_id`): 점검 배치. 컬럼: batch_id, room, period_start, period_end, reason, status(default 'open'), created_at.
- `inspection_scans` (PK 복합 `batch_id`+`reg_no`, FK batch_id→inspection_batches): 배치별 대조 결과 이력. 컬럼: batch_id, reg_no, status('scanned'/'not_found'/'not_in_db'), note, scanned_at, created_at. reg_no에 books FK 제약이 없어 not_in_db(DB에 없는 바코드)도 그대로 insert 가능.
- `disposal_candidates` (PK `id` bigint serial, FK batch_id→inspection_batches): 폐기 심의 후보. 컬럼: id, reg_no, reason, basis, batch_id, status(default 'pending_review'), created_at.

이 스키마는 이미 프로비저닝되어 있었음(2026-07-11 검증 테스트 시점 기준 0행 상태에서 시작). B-05의 `kdc_target_ratios`도 같은 프로젝트에 공존.

관련: [[project_2026-07-11_db_verification_test]]
