# MEMORY.md

- [장서 DB 스키마 현황 및 FN-03 제약](project_db_schema_status.md) — public.books 단일 테이블뿐, 대출/예약 이력 없어 FN-03은 항상 "판단 보류"
- [FN-02 유사도 계산 보정](feedback_fn02_similarity_calibration.md) — 유사도는 SQL 실측값만 사용(추정 금지), author 정규화 필수, 안전마진 70~85%로 조정
