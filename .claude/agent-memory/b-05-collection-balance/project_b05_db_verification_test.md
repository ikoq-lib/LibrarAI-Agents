---
name: project-b05-db-verification-test
description: Test rows inserted into kdc_target_ratios (300/800) on 2026-07-11 to verify real DB wiring — need deletion before production use
metadata:
  type: project
---

On 2026-07-11, ran an end-to-end DB verification of B-05 (FN-02 → FN-01 → FN-03) against the real Supabase backend (see [[reference_supabase_project]]). Inserted two rows into `public.kdc_target_ratios`:
- `('300', 18.0, '(테스트 검증용, 삭제 예정)')`
- `('800', 15.0, '(테스트 검증용, 삭제 예정)')`

**Why:** These are placeholder/test target ratios, not librarian-approved values (per the FN-02 human-in-the-loop rule, target ratios normally require explicit librarian sign-off — this was a wiring test, not a real registration).

**How to apply:** Before any real FN-02/FN-04 output is presented to a librarian, check whether these two rows still carry the `(테스트 검증용, 삭제 예정)` note. If so, flag them as non-authoritative and prompt the librarian to confirm or replace with real approved values — do not silently treat 18.0%/15.0% as the institution's actual targets. Delete them once the librarian provides real figures or explicitly confirms these test values coincidentally match the intended targets.

Verification results captured at that time (73,080 valid call_no rows, 000~900 all had holdings): current_pct 300=13.70%, 800=47.97%; with the test targets, deficiency_index 300=+4.30 (결핍), 800=-32.97 (큰 폭 과잉, 문학 편중).

**Update 2026-07-11 (same day):** Main session verified these two rows directly via SQL, then deleted them (`delete from public.kdc_target_ratios where note = '(테스트 검증용, 삭제 예정)'`). `public.kdc_target_ratios` is now empty (count=0) — no target ratios are registered yet. This is a real, still-open task: the librarian needs to provide actual approved target ratios before FN-02/FN-03/FN-04 can produce meaningful deficiency indices. The 13.70%/47.97% *current* holdings figures above remain accurate (computed straight from `public.books`, unaffected by the deletion) and are worth surfacing to the librarian as-is — the 800-class concentration (47.97% of the whole collection) is a genuine, notable finding independent of any target ratio.
