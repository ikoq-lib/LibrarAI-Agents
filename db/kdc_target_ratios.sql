-- ============================================================================
-- KDC 대분류 목표비율 등록 (public.kdc_target_ratios)
--
-- 출처: 「2026년 자료 확충 계획」 붙임 (A-01 ATT-006) "5. 자료 구입 산출 근거"
--   ※ 류별 확충 비율(D) = [(A)+(B)+(C)]/3
--       A = 전년 대출 도서 비율
--       B = 전년 도서 확충 비율
--       C = 전체 장서 현황 비율
--   ※ 류별 확충 권수(E) = (확충 예상 권수) x D / 100
--
-- 이 파일은 원문 산식을 우리 DB 실측값으로 재계산해 목표비율을 등록한다.
-- 매년 초 p_year 만 바꿔 재실행하면 그해 목표비율이 갱신된다.
--
-- 전제: db/acquisition_scoring.sql 적용 완료 (books.acquired_date, loans,
--       reg_no_num(), kdc_major_label, mv_kdc_deficit 존재).
--
-- 주의(2026-08-27): books 는 73,390권으로 ATT-006 원문의 전체 장서 117,669권과
--   44,279권 차이가 있다. 따라서 C(전체 장서 비율)는 우리가 가진 부분집합 기준이며,
--   빠진 장서의 류별 분포가 다르면 목표비율도 함께 달라진다. 장서 DB 정합성 확인 후
--   재실행할 것.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. 키 형식 정규화
--    mv_kdc_deficit 은 kdc_major 를 1자리('8')로 쓰는데
--    b-05-collection-balance.md 의 예시는 3자리('800')다.
--    3자리로 등록하면 조인이 조용히 어긋나 폴백이 그대로 유지되므로
--    입력 형식과 무관하게 첫 숫자 1자리로 저장되도록 강제한다.
-- ----------------------------------------------------------------------------

create or replace function public.kdc_target_normalize()
returns trigger language plpgsql as $$
begin
  new.kdc_major := substring(trim(new.kdc_major) from '^([0-9])');
  if new.kdc_major is null then
    raise exception 'kdc_major 에서 KDC 대분류 숫자를 읽을 수 없습니다: %', new.kdc_major;
  end if;
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists kdc_target_normalize_trg on public.kdc_target_ratios;
create trigger kdc_target_normalize_trg
  before insert or update on public.kdc_target_ratios
  for each row execute function public.kdc_target_normalize();

comment on function public.kdc_target_normalize() is
  'kdc_target_ratios.kdc_major 를 KDC 대분류 1자리로 정규화. '
  'B-05 문서의 3자리 표기("800")로 등록해도 mv_kdc_deficit 조인이 어긋나지 않게 한다.';


-- ----------------------------------------------------------------------------
-- 2. ATT-006 산식 계산 함수
--    p_year    : A(대출)·B(확충)의 기준 연도
--    p_lit_cap : 문학(8류) 상한. 산식 결과가 이 값을 넘으면 상한으로 자르고
--                초과분을 나머지 9개 류에 비례 배분한다. null 이면 상한 없음.
-- ----------------------------------------------------------------------------

create or replace function public.att006_target_ratios(
  p_year    int     default 2025,
  p_lit_cap numeric default null
)
returns table (
  kdc_major text,
  label     text,
  a_loan    numeric,   -- A: 해당 연도 대출 비율(%)
  b_acq     numeric,   -- B: 해당 연도 확충 비율(%)
  c_hold    numeric,   -- C: 전체 장서 비율(%)
  d_raw     numeric,   -- D: (A+B+C)/3, 원문 산식 그대로
  d_final   numeric    -- D 에 상한을 적용하고 합계 100 으로 맞춘 값
)
language sql stable as $$
  with a as (
    select substring(trim(bk.call_no) from '^([0-9])') as k, count(*)::numeric as n
    from public.loans l
    join public.books bk on public.reg_no_num(bk.reg_no) = public.reg_no_num(l.reg_no)
    where date_part('year', l.loan_date) = p_year and bk.call_no is not null
    group by 1
  ),
  b as (
    select substring(trim(call_no) from '^([0-9])') as k, count(*)::numeric as n
    from public.books
    where call_no is not null
      and acquired_date_precision = 'half_month'
      and date_part('year', acquired_date) = p_year
    group by 1
  ),
  c as (
    select substring(trim(call_no) from '^([0-9])') as k, count(*)::numeric as n
    from public.books
    where call_no is not null
    group by 1
  ),
  t as (
    select (select sum(n) from a) ta, (select sum(n) from b) tb, (select sum(n) from c) tc
  ),
  raw as (
    select km.code,
           km.label,
           coalesce(a.n, 0) / nullif((select ta from t), 0) * 100 as av,
           coalesce(b.n, 0) / nullif((select tb from t), 0) * 100 as bv,
           coalesce(c.n, 0) / nullif((select tc from t), 0) * 100 as cv
    from public.kdc_major_label km
    left join a on a.k = km.code
    left join b on b.k = km.code
    left join c on c.k = km.code
  ),
  d as (
    select code, label, av, bv, cv, (av + bv + cv) / 3 as dv from raw
  ),
  lit as (select dv from d where code = '8'),
  capped as (
    select code, label, av, bv, cv, dv,
           case
             when p_lit_cap is null or (select dv from lit) <= p_lit_cap then dv
             when code = '8' then p_lit_cap
             else dv * (100 - p_lit_cap) / nullif(100 - (select dv from lit), 0)
           end as fv
    from d
  ),
  -- 소수 2자리 반올림 잔차를 흡수시켜 합계를 정확히 100 으로 맞춘다.
  -- 상한이 걸린 문학에 흡수시키면 상한을 넘기므로, 상한 대상이 아닌 류 중
  -- 가장 큰 류(현재 사회과학)가 잔차를 받는다.
  rounded as (
    select code, label, av, bv, cv, dv, round(fv, 2) as fr from capped
  ),
  drift as (select 100 - sum(fr) as gap from rounded),
  absorber as (
    select code from rounded
    where p_lit_cap is null or code <> '8'
    order by fr desc, code
    limit 1
  )
  select r.code,
         r.label,
         round(r.av, 2),
         round(r.bv, 2),
         round(r.cv, 2),
         round(r.dv, 2),
         case when r.code = (select code from absorber)
              then r.fr + (select gap from drift)
              else r.fr end
  from rounded r
  order by r.code;
$$;

comment on function public.att006_target_ratios(int, numeric) is
  'ATT-006 「2026년 자료 확충 계획」의 류별 확충비율 산식 D=(A+B+C)/3 을 '
  'DB 실측값으로 재계산한다. p_year 는 A(대출)·B(확충) 기준연도, '
  'p_lit_cap 은 문학 상한(초과분은 나머지 9개 류에 비례 배분).';


-- ----------------------------------------------------------------------------
-- 3. 목표비율 등록
--    2026년분: 기준연도 2025, 문학 상한 50.0 (사서 확정 - 48~50% 유지 방향)
-- ----------------------------------------------------------------------------

insert into public.kdc_target_ratios (kdc_major, target_pct, note)
select kdc_major,
       d_final,
       format('ATT-006 산식 D=(A+B+C)/3 재계산 | A(2025대출) %s / B(2025확충) %s / C(전체장서) %s / D원값 %s | 문학상한 50.0 적용',
              a_loan, b_acq, c_hold, d_raw)
from public.att006_target_ratios(2025, 50.0)
on conflict (kdc_major) do update
  set target_pct = excluded.target_pct,
      note       = excluded.note,
      updated_at = now();


-- ----------------------------------------------------------------------------
-- 4. KDC 쿼터 배분 선정 함수 (ATT-006 E열 대응)
--
--    ※ 류별 확충 권수(E) = (확충 예상 권수) x D / 100
--
--    기존 acquisition_shortlist() 는 성인/어린이 쿼터만 적용하고 KDC 는 점수
--    가점으로만 반영한다. 그 결과 상위 100종의 78%가 문학이 되어 목표비율
--    50%가 지켜지지 않는다. 목표비율을 실제 권수 배분으로 강제하려면 이 함수를
--    쓴다.
--
--    배분: 류별 quota = round(총권수 x target_pct / 100), 최대잔여법으로 합계 보정.
--    선정: 류 안에서 score_total 내림차순.
--    주의: kdc_major 가 null 인 후보(부가기호 내용분류 없음)는 배분에서 빠진다.
-- ----------------------------------------------------------------------------

create or replace function public.acquisition_shortlist_kdc(
  p_total_n        integer default 100,
  p_max_month_diff integer default 15
)
returns setof public.v_candidate_scores
language sql
stable
as $$
  with q as (
    select kdc_major,
           target_pct,
           floor(p_total_n * target_pct / 100.0)          as base,
           p_total_n * target_pct / 100.0
             - floor(p_total_n * target_pct / 100.0)      as rem
    from public.kdc_target_ratios
  ),
  alloc as (
    select kdc_major,
           (base + case
                     when row_number() over (order by rem desc, kdc_major)
                          <= p_total_n - sum(base) over ()
                     then 1 else 0
                   end)::int as quota
    from q
  )
  select c.*
  from alloc a
  cross join lateral (
    select vc.*
    from public.v_candidate_scores vc
    where not vc.excluded
      and not vc.already_owned
      and vc.kdc_major = a.kdc_major
      and vc.month_diff between -1 and p_max_month_diff
    order by vc.score_total desc, vc.publish_predate desc
    limit a.quota
  ) c;
$$;

comment on function public.acquisition_shortlist_kdc(integer, integer) is
  'ATT-006 「자료 확충 계획」의 류별 확충 권수(E) 산식을 그대로 적용한 선정 목록. '
  'kdc_target_ratios 의 목표비율을 권수 쿼터로 강제한다(최대잔여법). '
  'acquisition_shortlist() 는 성인/어린이 쿼터만 적용하므로 KDC 비율이 지켜지지 않는다 - '
  '류별 비율을 맞춰야 하는 정기수서에는 이 함수를 쓸 것.';


-- ----------------------------------------------------------------------------
-- 5. 목표비율 등록으로 해소된 경고 주석 갱신
--    acquisition_scoring.sql 작성 시점에는 kdc_target_ratios 가 비어 있어
--    "폴백이 쏠림을 강화한다"는 경고를 달아 두었다. 이제 등록되었으므로 갱신한다.
-- ----------------------------------------------------------------------------

comment on materialized view public.mv_kdc_deficit is
  'KDC 대분류 결핍지수 = 목표비율 - 현재 소장비율. '
  '목표비율은 kdc_target_ratios(ATT-006 산식 D=(A+B+C)/3, 2026년분 등록 완료). '
  'target_registered=false 인 류가 생기면 그 류만 대출비율 폴백이 적용되므로 '
  'db/kdc_target_ratios.sql 을 재실행할 것.';

update public.scoring_weights
   set note = 'B-05 결핍지수 연동. 목표비율은 ATT-006 산식으로 등록됨(2026-08-27). '
              '주의 - 이 축은 점수 가점일 뿐 비율을 강제하지 않는다. '
              '류별 권수 비율을 맞추려면 acquisition_shortlist_kdc() 를 쓸 것.'
 where axis = 'kdc_balance';
