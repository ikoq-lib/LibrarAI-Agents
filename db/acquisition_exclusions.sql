-- ============================================================================
-- 수서 후보 배제 규칙
--
-- 배경(2026-08-27 테스트): SEOJI 수집분 9,873종으로 정기구입 583종을 뽑았더니
--   · 퍼플(교보 POD 자가출판) 75종(12.9%)
--   · 라이트노벨·만화 시리즈가 한 배치에 10권씩
--   · 자격증 수험서(SMAT, 한국사능력검정, 9급 공무원)
-- 가 그대로 선정됐다. 점수 축은 "우리 관에서 잘 나갈 책"은 잘 고르지만
-- "도서관이 사면 안 되는 책"을 거르지 못한다. 그 배제 규칙을 여기에 둔다.
--
-- 전제: db/acquisition_scoring.sql, db/kdc_target_ratios.sql 적용 완료.
--
-- 규칙은 전부 테이블에 있고 enabled 플래그로 켜고 끈다. 사서가 SQL 한 줄로
-- 조정할 수 있어야 하기 때문에 함수에 하드코딩하지 않는다.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. 출판사 배제 목록
--    match_type='contains' 는 원문 출판사명에 pattern 이 포함되는지(ilike),
--    'exact' 는 canon_publisher() 정규화 결과가 같은지 본다.
--    후보수/우리소장은 2026-08-27 카탈로그 9,873종 기준 실측값이다.
--    ※ 우리 관 소장 이력이 있는 곳(북랩 62권, 하움 16권)은 과거에 구입한
--      전례가 있으므로 넣지 않았다. 필요하면 사서가 추가한다.
-- ----------------------------------------------------------------------------

create table if not exists public.acquisition_excluded_publishers (
  id         serial primary key,
  pattern    text    not null,
  match_type text    not null default 'contains' check (match_type in ('contains', 'exact')),
  category   text    not null,
  reason     text    not null,
  enabled    boolean not null default true,
  added_at   timestamptz not null default now(),
  unique (pattern, match_type)
);

insert into public.acquisition_excluded_publishers (pattern, match_type, category, reason) values
  -- POD·자가출판: 저자가 비용을 내고 소량 등록한다. SEOJI 신간의 21.4%를 차지한다.
  ('부크크',       'contains', 'POD·자가출판', 'POD 자가출판 플랫폼 (후보 1,236종 / 우리 소장 5권)'),
  ('퍼플',         'contains', 'POD·자가출판', '교보문고 POD 자가출판 (후보 881종 / 우리 소장 2권)'),
  ('좋은땅',       'contains', 'POD·자가출판', '자비출판 (후보 60종 / 우리 소장 0권)'),
  ('지식과감성',   'contains', 'POD·자가출판', '자비출판 (후보 38종 / 우리 소장 0권)'),
  ('바른북스',     'contains', 'POD·자가출판', '자비출판 (후보 30종 / 우리 소장 0권)'),
  -- 수험서·학습교재 전문
  ('세진북스',     'contains', '수험서',       '기능사·산업기사 수험서 전문 (후보 190종 / 우리 소장 1권)'),
  ('제이원에듀',   'contains', '학습교재',     '영어 학습교재 전문 (후보 120종 / 우리 소장 0권)'),
  ('해커스',       'contains', '수험서',       '공무원·자격증 수험서 전문 (후보 79종 / 우리 소장 0권)'),
  ('박문각',       'contains', '수험서',       '공무원·전문자격 수험서 전문 (후보 67종 / 우리 소장 0권)'),
  -- 웹소설 분권: 5,000원짜리 권당 분책을 수십 권씩 등록한다.
  ('미스터블루',   'contains', '웹소설 분권', '장르 웹소설 권당 분책 (후보 150종 / 우리 소장 0권)'),
  ('더블플러스',   'contains', '웹소설 분권', '장르 웹소설 권당 분책 (후보 75종 / 우리 소장 0권)'),
  -- 비매품
  ('헵시바',       'contains', '비매품',       '외국어 선교 설교집, 정가 0원 (후보 140종 / 우리 소장 0권)')
on conflict (pattern, match_type) do update
  set category = excluded.category, reason = excluded.reason;

comment on table public.acquisition_excluded_publishers is
  '수서 후보에서 배제할 출판사. 끄려면 enabled=false, 추가하려면 insert. '
  '판단 근거는 reason 에 실측 후보수와 우리 소장 권수로 남긴다.';


-- ----------------------------------------------------------------------------
-- 2. 서명 배제 패턴 (수험서·자격증)
--    출판사 배제만으로는 일반 출판사가 낸 수험서를 못 거른다.
--    POSIX 정규식을 서명에 ~* 로 검사한다. 아래 종수는 2026-08-27 실측이다.
--
--    오탐을 피하려고 단독 단어는 쓰지 않는다.
--      · '기사'  -> '[가-힣]기사 + 필기|실기' 조합으로만 매칭
--      · '합격'  -> 미사용 (취업 에세이가 걸린다)
--      · '수험생' -> 미사용 ("수험생 자녀를 위한 비전기도문"이 걸렸다)
--      · '이기적' -> 미사용 ("이기적 유전자"가 걸린다. OA 패턴으로 대신 잡는다)
-- ----------------------------------------------------------------------------

create table if not exists public.acquisition_excluded_title_patterns (
  id       serial primary key,
  pattern  text    not null unique,
  category text    not null,
  reason   text    not null,
  enabled  boolean not null default true,
  added_at timestamptz not null default now()
);

insert into public.acquisition_excluded_title_patterns (pattern, category, reason) values
  ('한국사능력검정',
   '수험서', '한국사능력검정시험 대비서 (7종)'),
  ('(기능사|산업기사|기술사|[가-힣]기사)[[:space:]]*(필기|실기)',
   '수험서', '국가기술자격 필기·실기 대비서 (284종)'),
  ('공무원.*(시험|기본서|기출|모의고사|문제집)|[0-9]+급[[:space:]]*공무원',
   '수험서', '공무원 시험 대비서 (83종)'),
  ('(공인중개사|행정사|주택관리사|감정평가사|노무사|법무사|세무사|손해평가사)[[:space:]]*[0-9]*차?[[:space:]]*(시험|기본서|기출|모의고사|문제집|핵심)',
   '수험서', '전문자격 시험 대비서 (13종)'),
  ('기출문제|모의고사|실전[[:space:]]*모의',
   '수험서', '기출문제집·모의고사 (278종)'),
  ('SMAT|ITQ|GTQ|컴퓨터활용능력|정보처리(기사|산업기사)|워드프로세서',
   '수험서', 'OA·사무 자격 대비서 (16종)'),
  ('수험서|수험대비|시험대비',
   '수험서', '수험서임을 서명에 명시한 자료')
on conflict (pattern) do update
  set category = excluded.category, reason = excluded.reason;

comment on table public.acquisition_excluded_title_patterns is
  '서명 정규식으로 배제할 자료(주로 수험서). 어학 교재처럼 관에 따라 구입하는 '
  '유형은 행 단위로 enabled=false 하면 된다.';


-- ----------------------------------------------------------------------------
-- 3. 파라미터
--    series_max_per_batch : 한 배치에서 같은 시리즈를 몇 권까지 받을지
--    min_purchase_price   : 이 금액 미만은 구입 불가로 본다(0 이면 규칙 해제)
-- ----------------------------------------------------------------------------

insert into public.scoring_params (key, value, note) values
  ('series_max_per_batch', 3,
   '한 배치 내 동일 시리즈 상한. 시리즈명이 없으면 저자+출판사를 시리즈로 본다. '
   '실측 - 미적용 시 「무직전생」 10권, 「약사의 혼잣말」 7권이 한 배치에 들어왔다.'),
  ('min_purchase_price', 1,
   '정가가 이 값 미만이면 배제. 카탈로그의 827종(8.4%)이 정가 0원인 비매품이다. '
   '0 으로 두면 규칙이 꺼진다.')
on conflict (key) do update set value = excluded.value, note = excluded.note;


-- ----------------------------------------------------------------------------
-- 4. 배제 사유 판정 함수
--    통과하면 null, 걸리면 사유 문자열을 돌려준다.
--    사유를 남기는 이유 - 사서가 "왜 빠졌는지" 확인할 수 있어야 하기 때문이다.
-- ----------------------------------------------------------------------------

create or replace function public.acquisition_block_reason(
  p_publisher text,
  p_title     text,
  p_price     integer default null
)
returns text
language sql
stable
as $$
  select reason from (
    -- (1) 비매품·정가 미상
    select 1 as ord,
           format('비매품: 정가 %s원', coalesce(p_price, 0)) as reason
    where coalesce((select value from public.scoring_params where key = 'min_purchase_price'), 0) > 0
      and coalesce(p_price, 0) < (select value from public.scoring_params where key = 'min_purchase_price')

    union all
    -- (2) 출판사 배제
    select 2,
           format('%s 출판사 배제(%s): %s', ep.category, ep.pattern, ep.reason)
    from public.acquisition_excluded_publishers ep
    where ep.enabled
      and (
        (ep.match_type = 'contains' and coalesce(p_publisher, '') ilike '%' || ep.pattern || '%')
        or
        (ep.match_type = 'exact'
         and public.canon_publisher(p_publisher) = public.canon_publisher(ep.pattern))
      )

    union all
    -- (3) 서명 패턴 배제
    select 3,
           format('%s 서명 배제: %s', tp.category, tp.reason)
    from public.acquisition_excluded_title_patterns tp
    where tp.enabled
      and coalesce(p_title, '') ~* tp.pattern
  ) hits
  order by ord
  limit 1;
$$;

comment on function public.acquisition_block_reason(text, text, integer) is
  '수서 후보 배제 판정. 통과하면 null, 걸리면 사유 문자열. '
  '우선순위 - 비매품 > 출판사 > 서명 패턴.';


-- ----------------------------------------------------------------------------
-- 5. 배제된 후보 조회 뷰 (사서 검토용)
--    무엇이 왜 빠졌는지 볼 수 없으면 규칙을 못 고친다.
-- ----------------------------------------------------------------------------

create or replace view public.v_blocked_candidates as
select vc.ea_isbn,
       vc.title,
       vc.author,
       vc.publisher,
       vc.publish_predate,
       vc.pre_price,
       vc.주제,
       vc.대상,
       vc.score_total,
       public.acquisition_block_reason(vc.publisher, vc.title, vc.pre_price) as block_reason
from public.v_candidate_scores vc
where public.acquisition_block_reason(vc.publisher, vc.title, vc.pre_price) is not null;

comment on view public.v_blocked_candidates is
  '배제 규칙에 걸린 후보와 그 사유. 규칙이 과하게 잡는지 확인할 때 본다.';


-- ----------------------------------------------------------------------------
-- 6. 선정 함수 재정의 - 배제 규칙 + 시리즈 상한 적용
--    기존 (integer, integer) 시그니처는 없애고 시리즈 상한 인자를 더한다.
--    (create or replace 는 인자가 다르면 새 오버로드가 되어 호출이 모호해진다.)
-- ----------------------------------------------------------------------------

drop function if exists public.acquisition_shortlist_kdc(integer, integer);

create or replace function public.acquisition_shortlist_kdc(
  p_total_n        integer default 100,
  p_max_month_diff integer default 15,
  p_series_max     integer default null   -- null 이면 scoring_params.series_max_per_batch
)
returns setof public.v_candidate_scores
language sql
stable
as $$
  with lim as (
    select coalesce(
             p_series_max,
             (select value::int from public.scoring_params where key = 'series_max_per_batch'),
             3
           ) as series_max
  ),
  q as (
    select kdc_major,
           floor(p_total_n * target_pct / 100.0)     as base,
           p_total_n * target_pct / 100.0
             - floor(p_total_n * target_pct / 100.0) as rem
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
  ),
  pool as (
    select vc as v,
           vc.kdc_major,
           vc.score_total,
           vc.publish_predate,
           -- 시리즈명이 있으면 그것을, 없으면 저자+출판사를 한 묶음으로 본다.
           coalesce(
             nullif(trim(bc.series_title), ''),
             coalesce(vc.author_key, '?') || '|' || coalesce(vc.publisher_key, '?')
           ) as series_key
    from public.v_candidate_scores vc
    join public.book_catalog bc on bc.ea_isbn = vc.ea_isbn
    where not vc.excluded
      and not vc.already_owned
      and vc.month_diff between -1 and p_max_month_diff
      and public.acquisition_block_reason(vc.publisher, vc.title, vc.pre_price) is null
  ),
  series_capped as (
    select p.*,
           row_number() over (partition by p.series_key
                              order by p.score_total desc, p.publish_predate desc) as srn
    from pool p
  ),
  kdc_ranked as (
    select s.*,
           row_number() over (partition by s.kdc_major
                              order by s.score_total desc, s.publish_predate desc) as krn
    from series_capped s
    where s.srn <= (select series_max from lim)
  )
  select (k.v).*
  from kdc_ranked k
  join alloc a on a.kdc_major = k.kdc_major
  where k.krn <= a.quota;
$$;

comment on function public.acquisition_shortlist_kdc(integer, integer, integer) is
  'ATT-006 류별 확충 권수(E) 산식 + 배제 규칙 + 시리즈 상한을 적용한 선정 목록. '
  '배제 사유는 acquisition_block_reason() 이 판정하고 v_blocked_candidates 로 확인한다. '
  '시리즈 상한은 scoring_params.series_max_per_batch(기본 3).';


-- ----------------------------------------------------------------------------
-- 7. RLS - 규칙 테이블은 공개 읽기만
-- ----------------------------------------------------------------------------

alter table public.acquisition_excluded_publishers     enable row level security;
alter table public.acquisition_excluded_title_patterns enable row level security;

drop policy if exists excl_pub_read on public.acquisition_excluded_publishers;
create policy excl_pub_read on public.acquisition_excluded_publishers for select using (true);

drop policy if exists excl_title_read on public.acquisition_excluded_title_patterns;
create policy excl_title_read on public.acquisition_excluded_title_patterns for select using (true);
