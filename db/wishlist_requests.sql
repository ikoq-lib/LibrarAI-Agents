-- ============================================================================
-- B-02 희망도서 주간 신청 데이터
--
-- 연구용 데모 환경에서는 홈페이지 신청 폼이 없으므로, 주 1회(화요일) 액션 봇이
-- book_catalog 의 발행 30일 경과분에서 20~30권을 무작위로 뽑아 신청 건을 만든다.
--   scripts/generate-wishlist-requests.mjs
--   .github/workflows/generate-wishlist-requests.yml
--
-- 정기수서(B-01)와 달리 점수·가중치를 두지 않는다. 이용자의 신청은 장서 균형이나
-- 출판사 실적과 무관하게 흩어지므로, 가중치를 주면 오히려 실제 분포에서 멀어진다.
--
-- 반려 대상(수험서·5만원 초과·부적합 제본·5년 초과)도 걸러내지 않는다.
-- 실제 이용자도 반려 대상을 신청하며, B-02 의 R-01~R-10 판정이 일할 거리가 된다.
--
-- 개인정보:
--   신청자는 현재 전부 목업(테스트1, 테스트2 …)이지만, 이 테이블은 나중에 실제
--   신청이 들어오면 실명이 적재될 자리다. loans 와 같은 원칙으로 anon 공개 읽기
--   정책을 만들지 않는다 — 웹앱은 api/wishlist-requests.js 서버리스 함수를 통해서만
--   읽고, 그 함수가 이름 대신 표시용 라벨만 내려보낸다.
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. 신청자 고정 풀
--    매주 새 이름을 만들면 한 사람이 한 주에 한 번만 등장해 FN-04(1인 월 3권 한도)
--    검증이 항상 통과한다. 고정 풀에서 재사용해야 월 3권 초과가 자연히 발생한다.
-- ----------------------------------------------------------------------------
create table if not exists public.wishlist_patrons (
  id          serial primary key,
  name        text not null unique,
  age         int  not null check (age between 4 and 99),
  age_group   text not null check (age_group in ('유아','어린이','청소년','성인')),
  gender      text not null check (gender in ('남','여')),
  is_mock     boolean not null default true,
  created_at  timestamptz not null default now()
);

comment on table public.wishlist_patrons is
  'B-02 희망도서 신청자 풀. 현재는 전량 목업(테스트N). 고정 풀에서 재사용해야 1인 월 3권 한도 검증이 작동한다.';
comment on column public.wishlist_patrons.is_mock is
  '봇이 생성한 가상 신청자. 실제 이용자가 적재되면 false.';

-- ----------------------------------------------------------------------------
-- 2. 주간 신청 건
--    서지는 book_catalog 를 참조만 하지 않고 스냅샷으로 복사한다. 실제 신청은
--    book_catalog 에 없는 책일 수 있고, 신청 시점의 가격·제본형태가 보존돼야 한다.
-- ----------------------------------------------------------------------------
create table if not exists public.wishlist_requests (
  id            bigserial primary key,
  request_week  date not null,                 -- 접수 주차의 월요일(월~일 접수, 화요일 처리)
  requested_at  timestamptz not null,          -- 주 안에서 분산된 실제 신청 시각
  patron_id     int not null references public.wishlist_patrons(id),

  -- 서지 스냅샷. 열 구성은 사서 지정(title, author, ea_isbn, publisher, pre_price, form_detail).
  ea_isbn       text,
  title         text not null,
  author        text,
  publisher     text,
  pre_price     int,
  form_detail   text,

  source        text not null default 'mock',  -- mock | homepage | desk
  status        text not null default 'pending'
                check (status in ('pending','approved','rejected','manual_review')),
  reject_reason text,                          -- R-01 ~ R-10 판정 결과(B-02 가 기록)
  processed_at  timestamptz,
  created_at    timestamptz not null default now(),

  -- 같은 주에 같은 사람이 같은 책을 두 번 신청하지는 않는다.
  unique (request_week, patron_id, ea_isbn)
);

comment on table public.wishlist_requests is
  'B-02 희망도서 주간 신청 건. 봇이 화요일에 직전 월~일 접수분으로 생성한다. 서지는 book_catalog 스냅샷.';
comment on column public.wishlist_requests.request_week is
  '접수 주차의 월요일. B-02 는 이 주차 단위로 처리·보고한다.';
comment on column public.wishlist_requests.source is
  'mock=봇 생성, homepage=홈페이지 신청, desk=자료실 접수. 실제 신청이 들어와도 같은 테이블을 쓴다.';

create index if not exists wishlist_requests_week_idx  on public.wishlist_requests (request_week desc);
create index if not exists wishlist_requests_isbn_idx  on public.wishlist_requests (ea_isbn);
create index if not exists wishlist_requests_status_idx on public.wishlist_requests (status);

-- ----------------------------------------------------------------------------
-- 3. 주차별 요약 뷰 — FN-07 월간 현황·A-02 통계 응답에 쓴다.
-- ----------------------------------------------------------------------------
create or replace view public.v_wishlist_weekly as
select
  r.request_week,
  count(*)::int                                                as 신청건수,
  count(distinct r.patron_id)::int                             as 신청자수,
  count(*) filter (where r.status = 'approved')::int           as 구입대상,
  count(*) filter (where r.status = 'rejected')::int           as 반려,
  count(*) filter (where r.status = 'manual_review')::int      as 수동검토,
  count(*) filter (where r.status = 'pending')::int            as 미처리,
  sum(r.pre_price) filter (where r.status = 'approved')        as 구입예정액
from public.wishlist_requests r
group by r.request_week;

comment on view public.v_wishlist_weekly is
  'B-02 주차별 처리 현황. FN-05 주간 보고·FN-07 월간 현황의 집계 원본.';

-- ----------------------------------------------------------------------------
-- 4. 1인 월 N권 한도 점검 — FN-04.
--    반려 확정 건은 한도에서 빼지 않는다. 신청 시점 기준으로 세는 것이 규정이다.
--    월 경계는 KST 로 끊는다 — timestamptz 에 date_trunc 를 그냥 쓰면 세션 TimeZone 에
--    따라 답이 달라져, 월초·월말 자정 근처 신청이 접속 환경마다 다른 달로 잡힌다.
-- ----------------------------------------------------------------------------
create or replace view public.v_wishlist_monthly_quota as
select
  date_trunc('month', r.requested_at at time zone 'Asia/Seoul')::date as 신청월,
  p.name                                    as 신청자,
  p.age_group,
  count(*)::int                             as 신청권수,
  count(*) filter (where r.status = 'rejected')::int as 반려권수,
  (count(*) > 3)                            as 한도초과
from public.wishlist_requests r
join public.wishlist_patrons p on p.id = r.patron_id
group by 1, 2, 3;

comment on view public.v_wishlist_monthly_quota is
  'B-02 FN-04 검증용. 1인 월 3권 한도 초과 여부를 신청월×신청자로 집계한다.';

-- ----------------------------------------------------------------------------
-- 5. RLS
--    신청자 이름이 들어가는 테이블이므로 loans 와 같이 공개 읽기를 열지 않는다.
--    정책이 없으면 anon 은 차단되고 service_role 만 접근한다.
--    웹앱은 api/wishlist-requests.js(SUPABASE_DB_PASSWORD 직접 접속)로만 읽는다.
-- ----------------------------------------------------------------------------
alter table public.wishlist_patrons  enable row level security;
alter table public.wishlist_requests enable row level security;
