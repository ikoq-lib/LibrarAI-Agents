---
name: reference-supabase-project
description: Which Supabase project/tables B-05 actually reads from, and the schema of public.books / public.kdc_target_ratios
metadata:
  type: reference
---

B-05's real DB backend is Supabase project `tkyaganfdfiuesvbcbkr` (ACTIVE_HEALTHY, region ap-southeast-1, created 2026-07-11). There is a second project `jzoriabwegcnqxolzttq` (status INACTIVE, created 2026-03-22) that must NOT be used — it timed out on connection attempt and appears to be a stale/abandoned project from earlier testing.

**`public.books`** (73,390 rows as of 2026-07-11) — 장서 원부, grain = 등록번호(실물 1부). Comment: "whole_book_list.xlsx 기반 장서 원부. 등록번호(실물 1부) 단위 그레인." Relevant columns: `reg_no` (PK), `title`, `author`, `publisher`, `pub_year`, `loc_mark`, `call_no`, `vol`, `dup_no`, `room`, `shelf`, `material_status`, `loan_status`, `isbn`, `price`, `updated_at`.

**No dedicated KDC column exists.** KDC major class must be derived from `call_no` (청구기호), e.g. `"808.9 난812비 21"` → KDC major = first character of the trimmed string → `'8'` → label `'800'`. Verified all 73,080 non-null/non-empty call_no values start with a single digit 0-9 (no non-numeric prefixes), so `left(trim(call_no), 1) || '00'` is a safe, complete extraction — no fallback/exception handling needed for this dataset. 310 rows have NULL/empty call_no and are excluded from the denominator (2026-07-11 snapshot: 73,080 valid).

**`public.kdc_target_ratios`** — B-05-owned table for FN-02 target ratios. Columns: `kdc_major` (PK, text, e.g. "300"), `target_pct` (numeric), `note` (nullable text), `updated_at`. RLS enabled. Was empty (0 rows) until this 2026-07-11 session inserted test rows for 300/800 — see [[project_b05_db_verification_test]].

Use `mcp__supabase__execute_sql` with `project_id: "tkyaganfdfiuesvbcbkr"` for all B-05 real-DB queries.
