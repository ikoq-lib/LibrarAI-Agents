-- ============================================================================
-- B-01 수서 점수 스키마
-- 2026-08-25 생성.
--
-- 설계 원칙
--   1. 점수를 컬럼에 저장하지 않는다. 원본만 저장하고 점수는 뷰에서 계산한다.
--      -> 대출/소장 데이터가 갱신되면 다음 조회부터 자동 반영된다("유동적 점수").
--      -> 14.6만 행을 매일 UPDATE 할 필요가 없다(테이블 bloat / vacuum 부담 제거).
--   2. 무신호(미소장·미대출)에 0점이 아니라 중립값을 준다.
--      2026-07 신간 1,000종 측정 결과 45.8%가 출판사·저자 양쪽 모두 대출이력이 없다.
--      0점을 주면 신인 작가와 신생 출판사가 영구히 배제된다.
--   3. 회전율은 베이지안 축소(shrinkage)로 안정화한다.
--      소장 1권 출판사의 회전율은 표본이 1이라 신뢰할 수 없으므로 전체 평균 쪽으로 당긴다.
--      소장 저자의 80.4%가 1권짜리 롱테일이라 이 처리가 없으면 순위가 무너진다.
--   4. 가중치는 상수로 박지 않고 테이블에 둔다. 사서가 코드 수정 없이 조정할 수 있어야 한다.
--   5. 이용자 식별정보를 저장하지 않는다. 성명은 적재하지 않고 회원번호는 해시한다.
--
-- 선행 조건
--   public.books (73,390행), public.kdc_target_ratios, public.acquisition_candidates 존재.
--   books.acquired_date 는 이 파일이 추가하며, 실데이터는 아직 미확보 상태다.
-- ============================================================================


-- ============================================================================
-- 0. 확장
-- ============================================================================
create extension if not exists pgcrypto;   -- digest() : 회원번호 해시


-- ============================================================================
-- 1. 정규화 함수
--    출판사 정확일치는 26.5%에 그치지만 정규화 후 43.1%까지 오른다.
--    저자는 books가 '홍길동 지음' 형태로 저장돼 있어 역할어 제거가 필수다(정확일치 8.2%).
--    인덱스와 생성열에서 쓰려면 반드시 immutable 이어야 한다.
-- ============================================================================

create or replace function public.norm_publisher(p text)
returns text
language sql
immutable
as $$
  select nullif(
    regexp_replace(
      regexp_replace(
        lower(coalesce(p, '')),
        '\(주\)|\(사\)|주식회사|사단법인|재단법인|도서출판|출판사|출판그룹|퍼블리싱|publishing',
        '', 'g'),
      '[[:space:]·\-_.,''"]', '', 'g'),
    '');
$$;

comment on function public.norm_publisher(text) is
  '출판사명 정규화: 법인격·수식어·공백·구두점 제거 후 소문자화. (주)창비 = 창비 = 도서출판 창비';


create or replace function public.norm_author(a text)
returns text
language sql
immutable
as $$
  -- 1) SEOJI 접두어 '저자 : ' 제거
  -- 2) 다중저자 구분자(; , /)에서 첫 저자만 취함 - 대표저자 기준 집계
  -- 3) 역할어(지음/글/옮김/그림 등) 이후 절단
  -- 4) 공백·구두점 제거
  select nullif(
    regexp_replace(
      regexp_replace(
        regexp_replace(
          regexp_replace(coalesce(a, ''), '^[[:space:]]*저자[[:space:]]*:[[:space:]]*', ''),
          '[;,/].*$', ''),
        '[[:space:]]*(지음|엮음|옮김|편저|공저|편역|해설|감수|사진|원작|각색|글·그림|글그림|글|그림|저|편|역).*$', ''),
      '[[:space:]·\-_.,''"]', '', 'g'),
    '');
$$;

comment on function public.norm_author(text) is
  '저자명 정규화: SEOJI 접두어·역할어·공백 제거 후 대표저자 1인만 반환';


-- ============================================================================
-- 2. ISBN 부가기호 코드표
--    요구사항은 "숫자가 아닌 한글로 기록되는 대상/형태/주제 열"이었다.
--    한글 문자열을 14.6만 행에 중복 저장하는 대신 코드표를 조인해 뷰에서 노출한다.
--    분류표가 개정돼도 코드표 한 줄만 고치면 되고, 전체 UPDATE 가 발생하지 않는다.
--    뷰 v_book_catalog_ko 가 한글 열(대상/형태/주제)을 그대로 제공하므로 사용 측 체감은 동일하다.
-- ============================================================================

create table if not exists public.add_code_audience (
  code      varchar(1) primary key,
  label     text not null,
  age_group text not null,                   -- adult | youth | child | other : 성인/어린이 배분 기준
  collect   boolean not null default true,   -- false = 수집 단계에서 제외
  note      text
);

insert into public.add_code_audience (code, label, age_group, collect, note) values
  ('0', '교양',             'adult', true,  '일반 성인 교양서 - 수서 주력'),
  ('1', '실용',             'adult', true,  '요리/취미/자기계발 등. 일일 종이책의 13.1%'),
  ('2', '여성',             'adult', true,  '구분 폐지, 과거 자료에만 존재'),
  ('3', '(예비)',           'other', false, '미사용'),
  ('4', '청소년',           'youth', true,  '중고교 학습참고서 제외'),
  ('5', '중고교 학습참고서', 'youth', false, '공공도서관 미수집. 일일 종이책의 10.6%'),
  ('6', '초등 학습참고서',   'child', false, '공공도서관 미수집. 일일 종이책의 2.0%'),
  ('7', '아동',             'child', true,  '12세 이하 - 수서 주력'),
  ('8', '(예비)',           'other', false, '미사용'),
  ('9', '전문',             'adult', false, '학술·전문서. 일일 종이책의 11.5%')
on conflict (code) do update
  set label = excluded.label, age_group = excluded.age_group, note = excluded.note;

comment on table public.add_code_audience is
  'ISBN 부가기호 1자리(독자대상). collect=false 는 수집 단계에서 걸러낼 유형';


create table if not exists public.add_code_form (
  code    varchar(1) primary key,
  label   text not null,
  collect boolean not null default true,
  note    text
);

insert into public.add_code_form (code, label, collect, note) values
  ('0', '문고본',        true,  null),
  ('1', '사전',          true,  null),
  ('2', '신서판',        true,  null),
  ('3', '단행본',        true,  '수서 주력'),
  ('4', '전집·총서',     true,  '세트 구매 검토 필요'),
  ('5', '(예비)',        false, '미사용'),
  ('6', '도감',          true,  null),
  ('7', '그림책·만화',   true,  '학습만화 여부는 별도 판단(B-02 MANUAL_REVIEW)'),
  ('8', '혼합·전자자료', false, '종이책 수서 대상 아님'),
  ('9', '(예비)',        false, '미사용')
on conflict (code) do update
  set label = excluded.label, note = excluded.note;

comment on table public.add_code_form is 'ISBN 부가기호 2자리(발행형태)';


create table if not exists public.add_code_subject (
  code      varchar(3) primary key,   -- 부가기호 3~5자리 원본
  label     text not null,            -- 한글 주제명
  kdc_major varchar(1) not null,      -- KDC 대분류(첫 자리) - B-05 균형 연동 키
  note      text
);

-- 대분류 10개를 먼저 채운다(3자리 상세 코드는 운영하며 증분 등록).
-- 미등록 3자리 코드는 뷰에서 첫 자리로 대분류를 역산하므로 조회가 실패하지 않는다.
insert into public.add_code_subject (code, label, kdc_major, note) values
  ('000', '총류',     '0', '대분류 기본값'),
  ('100', '철학',     '1', '대분류 기본값'),
  ('200', '종교',     '2', '대분류 기본값'),
  ('300', '사회과학', '3', '대분류 기본값'),
  ('400', '자연과학', '4', '대분류 기본값'),
  ('500', '기술과학', '5', '대분류 기본값'),
  ('600', '예술',     '6', '대분류 기본값'),
  ('700', '언어',     '7', '대분류 기본값'),
  ('800', '문학',     '8', '대분류 기본값'),
  ('900', '역사',     '9', '대분류 기본값')
on conflict (code) do update
  set label = excluded.label, kdc_major = excluded.kdc_major;

comment on table public.add_code_subject is
  'ISBN 부가기호 3~5자리(내용분류). 미등록 코드는 첫 자리를 KDC 대분류로 역산해 사용';


create table if not exists public.kdc_major_label (
  code  varchar(1) primary key,
  label text not null
);

insert into public.kdc_major_label (code, label) values
  ('0','총류'),('1','철학'),('2','종교'),('3','사회과학'),('4','자연과학'),
  ('5','기술과학'),('6','예술'),('7','언어'),('8','문학'),('9','역사')
on conflict (code) do update set label = excluded.label;


-- ============================================================================
-- 3. book_catalog - SEOJI 일일 수집 원본
--    GitHub Action 이 매일 sort=INPUT_DATE&order_by=DESC 로 등록일 역순 페이지를 받아
--    워터마크(max(input_date) - 안전 소급일)에 도달할 때까지만 읽고 upsert 한다.
--    start_input_date 파라미터는 API 가 무시하지만 정렬은 동작하므로 증분 수집이 성립한다.
--    적재량: 종이책 등록 하루 750~900건. 미수집 유형(학습참고서/전문/전자자료 약 25%)을
--    걸러내면 연 20만 행 안팎 -> 약 90MB(인덱스 포함).
-- ============================================================================

create table if not exists public.book_catalog (
  ea_isbn         text primary key,             -- 낱권 ISBN13
  set_isbn        text,                         -- 세트 ISBN13
  title           text not null,
  author          text,
  series_title    text,
  series_no       text,                         -- SERIES_NO / SET_EXPRESSION / VOL 통합
  edition_stmt    text,
  publisher       text,
  publish_predate date,                         -- 발행예정일. 2022년 이후 실제 발행일과 100% 일치
  input_date      date,                         -- SEOJI 등록일(INPUT_DATE). 증분 수집 워터마크
  pre_price       integer,                      -- 예정가(원)
  form_detail     text,                         -- 무선제본/양장본/보드북 등
  page_count      integer,
  book_size       text,
  ea_add_code     varchar(5),                   -- 부가기호 원본 5자리

  -- 부가기호 분해(숫자). 한글 라벨은 v_book_catalog_ko 뷰에서 조인해 노출한다.
  add_code_audience varchar(1) generated always as (substring(ea_add_code from 1 for 1)) stored,
  add_code_form     varchar(1) generated always as (substring(ea_add_code from 2 for 1)) stored,
  add_code_subject  varchar(3) generated always as (substring(ea_add_code from 3 for 3)) stored,

  -- 조인 키(정규화). 생성열로 두어 원본과 어긋날 수 없게 한다.
  publisher_key   text generated always as (public.norm_publisher(publisher)) stored,
  author_key      text generated always as (public.norm_author(author)) stored,

  already_owned   boolean not null default false, -- 수집 시 books.isbn 대조 결과. B-03 부하 경감용
  excluded        boolean not null default false, -- 코드표 collect=false 등으로 사전 제외
  exclude_reason  text,

  first_seen      timestamptz not null default now(),
  last_seen       timestamptz not null default now(),
  raw             jsonb not null default '{}'::jsonb,

  constraint book_catalog_add_code_format
    check (ea_add_code is null or ea_add_code ~ '^[0-9]{5}$')
);

create index if not exists bc_predate_idx  on public.book_catalog (publish_predate desc);
create index if not exists bc_input_idx   on public.book_catalog (input_date desc);
create index if not exists bc_pubkey_idx   on public.book_catalog (publisher_key);
create index if not exists bc_autkey_idx   on public.book_catalog (author_key);
create index if not exists bc_audience_idx on public.book_catalog (add_code_audience);
create index if not exists bc_subject_idx  on public.book_catalog (add_code_subject);
create index if not exists bc_active_idx   on public.book_catalog (publish_predate desc)
  where excluded = false and already_owned = false;

comment on table public.book_catalog is
  'SEOJI 일일 수집 종이책 원본. 점수는 저장하지 않고 v_candidate_scores 에서 계산';


-- 한글 라벨 뷰 - 사용 측에서는 대상/형태/주제가 한글 열로 보인다.
create or replace view public.v_book_catalog_ko as
select
  bc.*,
  aud.label                     as 대상,
  aud.age_group                 as 대상구분,
  frm.label                     as 형태,
  coalesce(sub.label, km.label) as 주제,
  coalesce(sub.kdc_major, substring(bc.add_code_subject from 1 for 1)) as kdc_major
from public.book_catalog bc
left join public.add_code_audience aud on aud.code = bc.add_code_audience
left join public.add_code_form     frm on frm.code = bc.add_code_form
left join public.add_code_subject  sub on sub.code = bc.add_code_subject
left join public.kdc_major_label   km  on km.code  = substring(bc.add_code_subject from 1 for 1);


-- ============================================================================
-- 4. loans - 대출내역
--    원본 엑셀 131,773행(2024-01-01 ~ 2026-07-31, 고유 회원 5,567명, 고유 등록번호 39,798권).
--    이용자성명은 적재하지 않는다. 회원번호는 해시만 보관해 재식별을 막는다.
--    reg_no 로 public.books 와 80.5% 조인되고, 조인된 책의 99.6%가 ISBN 을 갖는다.
-- ============================================================================

create table if not exists public.loans (
  id             bigint generated always as identity primary key,
  member_hash    text,          -- sha256(회원번호 || salt). 원본 회원번호 저장 금지
  patron_type    text,          -- 일반여자/어린이남자/순회문고 등 원본 신분값
  age_group      text,          -- adult | child | youth | other  (patron_type 에서 파생)
  reg_no         text,          -- 등록번호 - books.reg_no 조인 키
  title_raw      text,          -- 대출 시점 서명(장서 미매칭 건의 최소 단서)
  loan_date      date not null,
  room           text,          -- 자료실
  call_no        text,          -- 청구기호
  source_library text,          -- 원본 10번째 열(헤더 없음). 정체 확인 전까지 원문 보관
  loaded_at      timestamptz not null default now()
);

create index if not exists loans_regno_idx on public.loans (reg_no);
create index if not exists loans_date_idx  on public.loans (loan_date);
create index if not exists loans_room_idx  on public.loans (room);
-- 같은 회원이 같은 책을 같은 날 중복 대출한 행은 없어야 한다(재적재 멱등성).
-- nulls not distinct (PG15+) 를 써야 회원번호나 등록번호가 빈 행도 중복 판정 대상이 된다.
-- 부분 인덱스로 두면 그 행들이 재적재 때마다 다시 들어간다.
create unique index if not exists loans_dedup_uidx
  on public.loans (member_hash, reg_no, loan_date, title_raw) nulls not distinct;

comment on table public.loans is
  '대출내역. 이용자 식별정보 저장 금지 - 성명 미적재, 회원번호는 해시. '
  '알려진 결손: 2025-12-14 ~ 2025-12-31 약 2,500건 누락(재추출 필요). '
  'source_library 는 2025-09~12 구간에만 존재하는 헤더 없는 열로, 의미 확인 전까지 원문 보관.';


-- 대출 데이터 기간 메타 - 노출기간 정규화의 기준점
create table if not exists public.loan_window (
  id         boolean primary key default true check (id),
  start_date date not null,
  end_date   date not null,
  note       text
);

insert into public.loan_window (id, start_date, end_date, note)
values (true, '2024-01-01', '2026-07-31', '초회 적재분. 2025-12-14~31 결손 있음')
on conflict (id) do update
  set start_date = excluded.start_date, end_date = excluded.end_date, note = excluded.note;


-- ============================================================================
-- 4-B. 등록번호 -> 등록시기 구간표
--    도서관은 등록번호를 입수 순서대로 매기므로, [시작등록번호, 끝등록번호] 구간이
--    곧 "그 기간에 입수된 도서"를 뜻한다. 실제 일자는 알 수 없고 반월 단위로만 확보돼
--    구간 중앙값(상반기=8일, 하반기=23일)을 추정일로 쓴다.
--    2019-01 ~ 2026-07 (161개 구간, EM161032~EM197374) 확보. 겹침·공백 없음이 확인됐다.
--    그 이전 등록번호는 2018년 도서관리시스템 교체 이전이라 자료가 없어 단일 대체값을 쓴다.
-- ============================================================================

-- 등록번호를 숫자로 정규화한다. EM181905 / EM0181905 처럼 자릿수 표기가 섞여 있으나
-- 숫자값은 전 구간에서 고유함을 확인했다(중복 0건). 인덱스에 쓰므로 immutable 이어야 한다.
create or replace function public.reg_no_num(r text)
returns bigint
language sql
immutable
as $$
  select case when r ~ '^EM[0-9]+$'
              then (regexp_replace(r, '^EM0*', ''))::bigint end;
$$;

comment on function public.reg_no_num(text) is
  '등록번호 EM접두어·선행 0 제거 후 숫자화. EM181905 = EM0181905 = 181905';

create index if not exists books_regnum_idx on public.books (public.reg_no_num(reg_no));

create table if not exists public.book_registration_periods (
  year      smallint not null,
  month     smallint not null check (month between 1 and 12),
  half      text     not null check (half in ('상', '하')),
  start_num bigint   not null,
  end_num   bigint   not null,
  est_date  date     not null,   -- 구간 중앙값(상=8일, 하=23일)
  primary key (year, month, half),
  constraint brp_range_order check (end_num >= start_num)
);

create index if not exists brp_range_idx on public.book_registration_periods (start_num, end_num);

comment on table public.book_registration_periods is
  '등록번호 구간별 입수 시기(반월 단위). scripts/load-acquisition-dates.mjs 가 적재한다. '
  'est_date 는 구간 중앙값 추정치이지 실제 등록일이 아니다.';


-- ============================================================================
-- 5. books 확장 - 자료 등록일
--    현재 books 에는 pub_year 만 있고 서가 투입 시점이 없다.
--    그래서 "2024년 발행 회전율 4.39"가 인기 때문인지 노출기간이 길어서인지 분리되지 않는다.
--    (2026년 발행분 회전율이 1.71로 낮게 나오는 것도 서가 체류가 짧아서다.)
--    acquired_date 가 채워지면 회전율이 노출기간으로 정규화돼 신간/구간 비교가 공정해진다.
--    2026-08-26 반월 단위 구간표로 42.5%(31,204권)를 채웠고, 나머지 2019년 이전분은
--    단일 대체값이다. 여전히 null 인 행은 발행연도 7월 1일로 근사한다.
-- ============================================================================

alter table public.books add column if not exists acquired_date date;
alter table public.books add column if not exists acquired_date_precision text;
create index if not exists books_acquired_idx on public.books (acquired_date);

comment on column public.books.acquired_date is
  '자료 등록일 추정치. 회전율의 노출기간 정규화에 사용. 실제 일자가 아니라 '
  'book_registration_periods 의 반월 구간 중앙값이다.';

comment on column public.books.acquired_date_precision is
  'half_month  = 반월 구간 중앙값(오차 최대 ±8일). '
  'pre_2019    = 2019-01 이전 등록번호. 자료가 없어 단일 대체값을 넣은 것으로 시기 정보 없음. '
  'null        = 등록번호가 구간표에 없어 미배정.';


-- ============================================================================
-- 6. publisher_aliases - 표기 흔들림 수동 보정
--    norm_publisher() 로 흡수되지 않는 이형(미래엔아이세움 = 아이세움 = Mirae N 아이세움)을 묶는다.
--    실측에서 이 3개가 각각 회전율 16.3 / 9.4 / 10.5 로 흩어져 있었다.
-- ============================================================================

create table if not exists public.publisher_aliases (
  alias_key     text primary key,   -- norm_publisher() 결과
  canonical_key text not null,      -- 대표 표기의 norm_publisher() 결과
  note          text
);

insert into public.publisher_aliases (alias_key, canonical_key, note) values
  (public.norm_publisher('미래엔아이세움'),  public.norm_publisher('아이세움'), '동일 임프린트'),
  (public.norm_publisher('Mirae N 아이세움'), public.norm_publisher('아이세움'), '동일 임프린트'),
  (public.norm_publisher('미래엔'),          public.norm_publisher('아이세움'), '동일 그룹 - 분리하려면 이 행 삭제')
on conflict (alias_key) do nothing;

create or replace function public.canon_publisher(p text)
returns text
language sql
stable
as $$
  select coalesce(
    (select a.canonical_key from public.publisher_aliases a
      where a.alias_key = public.norm_publisher(p)),
    public.norm_publisher(p));
$$;


-- ============================================================================
-- 7. 가중치 / 점수 구간 - 코드 수정 없이 사서가 조정
-- ============================================================================

create table if not exists public.scoring_weights (
  axis          text primary key,
  max_points    numeric not null check (max_points >= 0),
  neutral_ratio numeric not null default 0.5 check (neutral_ratio between 0 and 1),
  enabled       boolean not null default true,
  note          text
);

-- 배분 근거
--   발행일 20  : 측정된 최강 단일 예측변수(2014년 발행 회전율 0.53 vs 2024년 4.39 = 8.3배)
--   출판사 20 / 저자 20 : 소장규모와 회전율을 축 하나로 결합해 이중계산을 막는다
--                        (많이 산 출판사가 많이 대출되는 것은 같은 신호다)
--   외부인기 15 : 주간 harvest(교보/YES24/KPIPA)의 recommend_count. 원안에 없던 축.
--                 이 축이 없으면 "우리 도서관의 과거 이력"만 보게 된다
--   KDC결핍 15  : B-05 결핍지수. 대형 출판사 쏠림(마태효과)을 상쇄하는 유일한 축
--   가격 10     : 원안 유지. 변별력은 낮으나(71.9%가 한 구간) 이상치 제거 장치
insert into public.scoring_weights (axis, max_points, neutral_ratio, note) values
  ('publisher',   20, 0.50, '조정회전율 백분위. 무신호는 중앙값 처리'),
  ('author',      20, 0.50, '조정회전율 백분위. 무신호는 중앙값 처리'),
  ('pubdate',     20, 0.20, 'pubdate_score_bands 참조'),
  ('popularity',  15, 0.00, 'acquisition_candidates.recommend_count 연동. 미등장은 0(가점 방식)'),
  ('kdc_balance', 15, 0.50, 'B-05 결핍지수 연동. kdc_target_ratios 미등록 시 폴백이 역효과 - mv_kdc_deficit 주석 참조'),
  ('price',       10, 0.50, 'price_score_bands 참조')
on conflict (axis) do update
  set max_points = excluded.max_points, neutral_ratio = excluded.neutral_ratio, note = excluded.note;


-- 발행일 점수 구간
--   month_diff = (당월 - 발행예정월), 단위 개월. 음수 = 미래 발행.
--   원안(현재 8월 기준 6~9월 20점 / 3~5월 16 / 전년12~2월 12 / 전년9~11월 8 / 이전 4)을 그대로 옮겼다.
--   미래 2개월 이상(CIP 사전등록분)은 원안에 없던 구간이라 별도 처리했다.
create table if not exists public.pubdate_score_bands (
  id       smallint primary key,
  diff_min integer not null,    -- month_diff 하한(포함)
  diff_max integer not null,    -- month_diff 상한(포함)
  points   numeric not null,
  label    text not null
);

insert into public.pubdate_score_bands (id, diff_min, diff_max, points, label) values
  (1, -120,   -2, 10, '출간 예정(2개월 이상 후) - 아직 구매 불가, 예약 검토 대상'),
  (2,   -1,    2, 20, '최근 3개월 + 1개월 후'),
  (3,    3,    5, 16, '그 이전 3개월'),
  (4,    6,    8, 12, '그 이전 3개월'),
  (5,    9,   11,  8, '그 이전 3개월'),
  (6,   12, 9999,  4, '1년 초과')
on conflict (id) do update
  set diff_min = excluded.diff_min, diff_max = excluded.diff_max,
      points = excluded.points, label = excluded.label;


-- 가격 점수 구간 (원안 유지)
create table if not exists public.price_score_bands (
  id        smallint primary key,
  min_price integer not null,
  max_price integer not null,
  points    numeric not null,
  label     text not null
);

insert into public.price_score_bands (id, min_price, max_price, points, label) values
  (1,     0,    9999,  5, '1만원 미만 (후보의 22.0%)'),
  (2, 10000,   39999, 10, '1만~4만원 (후보의 71.9%)'),
  (3, 40000, 9999999,  5, '4만원 이상 (후보의 6.1%)')
on conflict (id) do update
  set min_price = excluded.min_price, max_price = excluded.max_price,
      points = excluded.points, label = excluded.label;


-- 베이지안 축소 파라미터
create table if not exists public.scoring_params (
  key   text primary key,
  value numeric not null,
  note  text
);

insert into public.scoring_params (key, value, note) values
  ('shrink_m_publisher', 5, '출판사 회전율 축소 강도. 소장이 적으면 전체평균 쪽으로 당김'),
  ('shrink_m_author',    3, '저자 회전율 축소 강도. 저자의 80.4%가 소장 1권이라 더 강하게 필요'),
  ('popularity_full',    4, 'recommend_count 가 이 값 이상이면 인기 축 만점')
on conflict (key) do update set value = excluded.value, note = excluded.note;


-- ============================================================================
-- 8. 통계 머티리얼라이즈드 뷰 - 야간 1회 갱신
--    책 단위 노출기간(book-month)으로 정규화한 연환산 회전율을 만들고,
--    베이지안 축소를 적용한 뒤 백분위(0~1)로 환산한다.
--
--    축소식:  adj = (대출수*12 + m*prior) / (book_months + m*12)
--      prior = 전체 평균 회전율(권당 연간 대출수)
--      소장이 많을수록 자기 실적이, 적을수록 prior 가 지배한다.
--      -> 소장 1권 출판사가 우연히 1회 대출됐다고 상위로 튀지 않는다.
-- ============================================================================

-- 8-1. 책 단위 대출 집계 + 노출기간
drop materialized view if exists public.mv_book_usage cascade;
create materialized view public.mv_book_usage as
with w as (select start_date, end_date from public.loan_window where id)
select
  b.reg_no,
  public.canon_publisher(b.publisher)        as publisher_key,
  public.norm_author(b.author)               as author_key,
  substring(trim(b.call_no) from '^([0-9])') as kdc_major,
  count(l.id)                                as loan_count,
  -- 노출기간(개월): 대출데이터 시작일과 자료 등록일 중 늦은 쪽부터 데이터 종료일까지.
  -- acquired_date 가 없으면 발행연도 7월 1일로 근사한다(확보 시 자동으로 정확해짐).
  greatest(
    1.0,
    extract(epoch from (
      (select end_date from w)::timestamp
      - greatest(
          (select start_date from w),
          coalesce(b.acquired_date, make_date(coalesce(b.pub_year, 1900), 7, 1))
        )::timestamp
    )) / 2629746.0        -- 초 -> 평균 개월(30.44일)
  )::numeric              as exposure_months
from public.books b
left join public.loans l on l.reg_no = b.reg_no
group by b.reg_no, b.publisher, b.author, b.call_no, b.acquired_date, b.pub_year;

create unique index mv_book_usage_uidx    on public.mv_book_usage (reg_no);
create index        mv_book_usage_pub_idx on public.mv_book_usage (publisher_key);
create index        mv_book_usage_aut_idx on public.mv_book_usage (author_key);
create index        mv_book_usage_kdc_idx on public.mv_book_usage (kdc_major);


-- 8-2. 출판사 통계
drop materialized view if exists public.mv_publisher_stats cascade;
create materialized view public.mv_publisher_stats as
with agg as (
  select publisher_key,
         count(*)             as holdings,
         sum(loan_count)      as loans,
         sum(exposure_months) as book_months
  from public.mv_book_usage
  where publisher_key is not null
  group by publisher_key
),
prior as (
  select sum(loans) * 12.0 / nullif(sum(book_months), 0) as p from agg
),
m as (
  select value as v from public.scoring_params where key = 'shrink_m_publisher'
),
shrunk as (
  select a.publisher_key, a.holdings, a.loans, a.book_months,
         a.loans * 12.0 / nullif(a.book_months, 0) as raw_turnover,
         (a.loans * 12.0 + (select v from m) * (select p from prior))
           / nullif(a.book_months + (select v from m) * 12.0, 0) as adj_turnover
  from agg a
)
select publisher_key, holdings, loans, book_months,
       round(raw_turnover, 3)                     as raw_turnover,
       round(adj_turnover, 3)                     as adj_turnover,
       (percent_rank() over (order by adj_turnover))::numeric as pct_rank
from shrunk;

create unique index mv_pub_stats_uidx on public.mv_publisher_stats (publisher_key);


-- 8-3. 저자 통계
drop materialized view if exists public.mv_author_stats cascade;
create materialized view public.mv_author_stats as
with agg as (
  select author_key,
         count(*)             as holdings,
         sum(loan_count)      as loans,
         sum(exposure_months) as book_months
  from public.mv_book_usage
  where author_key is not null
  group by author_key
),
prior as (
  select sum(loans) * 12.0 / nullif(sum(book_months), 0) as p from agg
),
m as (
  select value as v from public.scoring_params where key = 'shrink_m_author'
),
shrunk as (
  select a.author_key, a.holdings, a.loans, a.book_months,
         a.loans * 12.0 / nullif(a.book_months, 0) as raw_turnover,
         (a.loans * 12.0 + (select v from m) * (select p from prior))
           / nullif(a.book_months + (select v from m) * 12.0, 0) as adj_turnover
  from agg a
)
select author_key, holdings, loans, book_months,
       round(raw_turnover, 3)                     as raw_turnover,
       round(adj_turnover, 3)                     as adj_turnover,
       (percent_rank() over (order by adj_turnover))::numeric as pct_rank
from shrunk;

create unique index mv_aut_stats_uidx on public.mv_author_stats (author_key);


-- 8-4. KDC 대분류 결핍지수 (B-05 연동)
--    결핍 = 목표비율 - 현재 소장비율. 회전율이 높은데 소장이 적은 분야에 가점한다.
--    kdc_target_ratios 가 비어 있는 현재는 대출비율을 목표로 간주한다(수요 기반 폴백).
--    실측: 자연과학 회전율 3.17 / 언어 3.11 (과소), 기술과학 1.20 / 사회과학 1.37 (과다)
drop materialized view if exists public.mv_kdc_deficit cascade;
create materialized view public.mv_kdc_deficit as
with holdings as (
  select kdc_major,
         count(*)::numeric             as h,
         sum(loan_count)::numeric      as l,
         sum(exposure_months)::numeric as bm
  from public.mv_book_usage
  where kdc_major is not null
  group by kdc_major
),
tot as (select sum(h) th, sum(l) tl from holdings)
select h.kdc_major,
       h.h::bigint                            as holdings,
       round(h.h / t.th, 4)                   as holding_ratio,
       round(h.l / nullif(t.tl, 0), 4)        as loan_ratio,
       round(h.l * 12.0 / nullif(h.bm, 0), 3) as turnover,
       round(coalesce(kt.target_pct / 100.0, h.l / nullif(t.tl, 0)) - h.h / t.th, 4) as deficit,
       (kt.target_pct is not null)            as target_registered
from holdings h
cross join tot t
left join public.kdc_target_ratios kt on kt.kdc_major = h.kdc_major;

create unique index mv_kdc_deficit_uidx on public.mv_kdc_deficit (kdc_major);

comment on materialized view public.mv_kdc_deficit is
  'KDC 대분류 결핍지수. target_registered=false 는 목표비율 미등록으로 대출비율을 대체 목표로 쓴 것. '
  '경고 - 이 폴백 상태에서는 "많이 대출되는 분야 = 결핍"이 되어 문학에 최고 결핍(+0.0516)이 부여된다. '
  '즉 쏠림을 막으려는 축이 오히려 쏠림을 강화한다. kdc_target_ratios 등록 전에는 '
  'scoring_weights 에서 kdc_balance 를 enabled=false 로 두는 편이 안전하다.';


-- ============================================================================
-- 9. v_candidate_scores - 최종 점수 뷰
--    점수를 저장하지 않고 조회 시점에 계산한다.
--    발행일 점수는 current_date 기준이라 달이 바뀌면 자동 갱신되고,
--    출판사/저자 점수는 MV 를 갱신하는 순간 다음 조회부터 반영된다.
--    -> "대출이 늘면 점수가 오른다"가 UPDATE 없이 성립한다.
-- ============================================================================

create or replace view public.v_candidate_scores as
with w as (
  select axis, max_points, neutral_ratio from public.scoring_weights where enabled
),
base as (
  select
    bc.ea_isbn, bc.set_isbn, bc.title, bc.author, bc.publisher, bc.publish_predate,
    bc.pre_price, bc.form_detail, bc.page_count, bc.book_size,
    bc.series_title, bc.series_no, bc.edition_stmt,
    bc.ea_add_code, bc.add_code_audience, bc.add_code_subject,
    bc.already_owned, bc.excluded,
    aud.label     as 대상,
    aud.age_group as 대상구분,
    frm.label     as 형태,
    coalesce(sub.label, km.label) as 주제,
    coalesce(sub.kdc_major, substring(bc.add_code_subject from 1 for 1)) as kdc_major,
    public.canon_publisher(bc.publisher) as publisher_key,
    bc.author_key,
    -- 당월 - 발행예정월, 단위 개월. 음수 = 아직 발행 전
    ( (extract(year  from current_date)::int * 12 + extract(month from current_date)::int)
    - (extract(year  from bc.publish_predate)::int * 12 + extract(month from bc.publish_predate)::int)
    )::int as month_diff
  from public.book_catalog bc
  left join public.add_code_audience aud on aud.code = bc.add_code_audience
  left join public.add_code_form     frm on frm.code = bc.add_code_form
  left join public.add_code_subject  sub on sub.code = bc.add_code_subject
  left join public.kdc_major_label   km  on km.code  = substring(bc.add_code_subject from 1 for 1)
),
scored as (
  select
    b.*,
    ps.holdings      as pub_holdings,
    ps.loans         as pub_loans,
    ps.adj_turnover  as pub_turnover,
    aus.holdings     as aut_holdings,
    aus.loans        as aut_loans,
    aus.adj_turnover as aut_turnover,
    kd.deficit       as kdc_deficit,
    ac.recommend_count,
    ac.sources       as popularity_sources,

    -- 출판사: 백분위 x 만점. 무신호는 neutral_ratio(기본 0.5) x 만점 = 중앙값 대우.
    round(coalesce(ps.pct_rank, (select neutral_ratio from w where axis = 'publisher'))
          * (select max_points from w where axis = 'publisher'), 2) as score_publisher,

    -- 저자: 동일
    round(coalesce(aus.pct_rank, (select neutral_ratio from w where axis = 'author'))
          * (select max_points from w where axis = 'author'), 2) as score_author,

    -- 발행일: 구간표 조회. 발행일 자체가 없으면 neutral.
    round(coalesce(
      (select pb.points from public.pubdate_score_bands pb
        where b.month_diff between pb.diff_min and pb.diff_max
        order by pb.id limit 1),
      (select max_points * neutral_ratio from w where axis = 'pubdate')), 2) as score_pubdate,

    -- 가격: 구간표 조회. 가격 미상은 neutral.
    round(coalesce(
      (select pr.points from public.price_score_bands pr
        where b.pre_price between pr.min_price and pr.max_price
        order by pr.id limit 1),
      (select max_points * neutral_ratio from w where axis = 'price')), 2) as score_price,

    -- 외부 인기신호: 주간 harvest 추천 소스 수. popularity_full(기본 4) 이상이면 만점.
    -- 이 축만 가점 방식이다(미등장 = 0). 대다수 신간은 어느 매체에도 안 잡히기 때문에
    -- 중립값을 주면 축 자체가 무의미해진다.
    round(least(coalesce(ac.recommend_count, 0)
                / nullif((select value from public.scoring_params where key = 'popularity_full'), 0), 1.0)
          * (select max_points from w where axis = 'popularity'), 2) as score_popularity,

    -- KDC 결핍: 결핍이 클수록 가점. -0.05 ~ +0.05 를 0 ~ 만점으로 선형 사상.
    round(greatest(0, least(1, (coalesce(kd.deficit, 0) + 0.05) / 0.10))
          * (select max_points from w where axis = 'kdc_balance'), 2) as score_kdc

  from base b
  left join public.mv_publisher_stats     ps  on ps.publisher_key = b.publisher_key
  left join public.mv_author_stats        aus on aus.author_key   = b.author_key
  left join public.mv_kdc_deficit         kd  on kd.kdc_major     = b.kdc_major
  left join public.acquisition_candidates ac  on ac.isbn          = b.ea_isbn
)
select
  s.*,
  round(s.score_publisher + s.score_author + s.score_pubdate
      + s.score_price + s.score_popularity + s.score_kdc, 2) as score_total,
  -- 신호 없는 축의 개수. 클수록 총점의 근거가 얕다는 표시.
  ( (case when s.pub_holdings   is null then 1 else 0 end)
  + (case when s.aut_holdings   is null then 1 else 0 end)
  + (case when s.recommend_count is null then 1 else 0 end) ) as unknown_axes
from scored s;

comment on view public.v_candidate_scores is
  'B-01 수서 후보 점수. 저장하지 않고 조회 시점 계산 - MV 갱신 즉시 반영. '
  'unknown_axes 가 2 이상이면 총점을 단독 근거로 쓰지 말 것(신간의 45.8%가 여기 해당)';


-- 9-1. B-01 추천 함수 - 성인/어린이 배분 쿼터를 적용해 상위 N건만 반환
--      B-01 에는 이 결과만 전달한다. 후보 풀 전체를 모델에 넣지 않으므로 토큰이 크게 준다.
create or replace function public.acquisition_shortlist(
  p_adult_n        integer default 60,
  p_child_n        integer default 40,
  p_max_month_diff integer default 15
)
returns setof public.v_candidate_scores
language sql
stable
as $$
  (select * from public.v_candidate_scores
    where not excluded and not already_owned
      and 대상구분 = 'adult'
      and month_diff between -1 and p_max_month_diff
    order by score_total desc, publish_predate desc
    limit p_adult_n)
  union all
  (select * from public.v_candidate_scores
    where not excluded and not already_owned
      and 대상구분 = 'child'
      and month_diff between -1 and p_max_month_diff
    order by score_total desc, publish_predate desc
    limit p_child_n);
$$;

comment on function public.acquisition_shortlist(integer, integer, integer) is
  '성인/어린이 쿼터를 적용한 수서 후보 상위 목록. 배분 기준은 부가기호 1자리(대상). '
  '기본 60:40. 참고 - 실측 대출 비중은 회원 신분 기준 성인 66.9% / 어린이 26.8% / 학생 6.3%, '
  '자료실 기준으로는 어린이 계열이 더 많다(성인 회원이 자녀 책을 대출하기 때문).';


-- ============================================================================
-- 10. 갱신 함수 - GitHub Action 이 일일 수집 직후 1회 호출
-- ============================================================================

-- 주의: REFRESH MATERIALIZED VIEW CONCURRENTLY 는 함수/트랜잭션 블록 안에서 실행할 수 없다.
-- 따라서 이 함수는 일반 refresh 를 쓴다(갱신 중 해당 MV 는 ACCESS EXCLUSIVE 로 잠긴다. 수 초 수준).
-- 조회를 막지 않으려면 scripts/load-loans.mjs 처럼 트랜잭션 밖에서 아래를 직접 실행할 것:
--   refresh materialized view concurrently public.mv_book_usage;
--   refresh materialized view concurrently public.mv_publisher_stats;
--   refresh materialized view concurrently public.mv_author_stats;
--   refresh materialized view concurrently public.mv_kdc_deficit;
-- (순서 중요 - mv_book_usage 가 나머지 셋의 원본이다.)
create or replace function public.refresh_acquisition_stats()
returns void
language plpgsql
as $$
begin
  refresh materialized view public.mv_book_usage;
  refresh materialized view public.mv_publisher_stats;
  refresh materialized view public.mv_author_stats;
  refresh materialized view public.mv_kdc_deficit;
end;
$$;

comment on function public.refresh_acquisition_stats() is
  '통계 MV 일괄 갱신(비동시). 갱신 중 조회를 막지 않으려면 트랜잭션 밖에서 '
  'refresh materialized view concurrently 를 직접 실행할 것 - 함수 안에서는 불가능하다.';


-- ============================================================================
-- 11. RLS / 권한
--    loans 는 공개 읽기를 열지 않는다(집계 MV 로만 노출).
--    나머지는 웹앱 anon 읽기 허용, 쓰기는 service_role 전용(정책 없음 = 차단).
-- ============================================================================

alter table public.book_catalog        enable row level security;
alter table public.loans               enable row level security;
alter table public.add_code_audience   enable row level security;
alter table public.add_code_form       enable row level security;
alter table public.add_code_subject    enable row level security;
alter table public.kdc_major_label     enable row level security;
alter table public.publisher_aliases   enable row level security;
alter table public.scoring_weights     enable row level security;
alter table public.pubdate_score_bands enable row level security;
alter table public.price_score_bands   enable row level security;
alter table public.scoring_params      enable row level security;
alter table public.loan_window         enable row level security;

do $$
declare t text;
begin
  foreach t in array array[
    'book_catalog','add_code_audience','add_code_form','add_code_subject',
    'kdc_major_label','publisher_aliases','scoring_weights',
    'pubdate_score_bands','price_score_bands','scoring_params','loan_window'
  ] loop
    execute format('drop policy if exists %I on public.%I', t || ' public read', t);
    execute format('create policy %I on public.%I for select using (true)', t || ' public read', t);
  end loop;
end
$$;

-- loans 에는 select 정책을 만들지 않는다 -> anon 접근 차단, service_role 만 접근 가능.

grant select on public.mv_publisher_stats, public.mv_author_stats,
                public.mv_kdc_deficit to anon, authenticated;
-- mv_book_usage 는 등록번호 단위라 노출하지 않는다.
