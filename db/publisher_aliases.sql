-- ============================================================================
-- publisher_aliases - 출판사 이형 표기 별칭
-- 2026-08-27 생성. db/acquisition_scoring.sql 다음에 실행한다.
--
-- 왜 필요한가
--   수서 점수의 출판사 축(24점)은 "그 출판사 책이 우리 관에서 얼마나 도는가"를 본다.
--   후보(SEOJI)와 소장(books)의 출판사명이 붙어야 계산이 되는데 두 단계에서 어긋난다.
--
--   1단계 - 표기 흔들림. '(주식회사)창비' vs '창비'.
--           norm_publisher() 가 처리한다. 2026-08-27 재작성으로 46.2% -> 56.1%.
--           이 파일이 아니라 db/acquisition_scoring.sql 의 몫이다.
--
--   2단계 - 이름 자체가 다름. SEOJI 는 법인명으로 등록하는데 우리 장서는 임프린트명으로
--           들어와 있다. '(주식회사)북21' 과 '21세기북스/아울북/을파소/아르테' 가 그렇다.
--           문자열로는 절대 못 붙는다. 이 파일이 사람 손으로 묶는다.
--
-- 어떻게 찾았나 (재현 절차)
--   가. 배제 규칙을 통과한 후보 중 소장 이력이 안 붙는 출판사를 권수 순으로 뽑는다.
--       (아래 "점검 쿼리 1")
--   나. 각 출판사의 ISBN 앞 8자리(978/979 + 국별기호 + 발행자기호 일부)가 소장측에
--       존재하는지 본다. 같은 발행자기호 = 같은 등록 주체다.
--   다. 다만 발행자기호가 4~5자리인 중소 출판사는 8자리 절단으로 남의 구간과 섞인다.
--       실제로 '(주)잉글리시에그' 가 미래엔 계열로, '데카 미디어' 가 사파리로 잘못 걸렸다.
--       그래서 접두 일치는 후보를 좁히는 데만 쓰고, 등재는 사람이 확인한 것만 한다.
--   라. 확인 결과 '(주)서울미디어코믹스'(후보 36권)는 소장 0권이라 별칭이 아니라
--       진짜 신규 출판사였다. 짐작으로 넣지 않는다.
--
-- 임프린트를 묶는 게 맞나
--   아울북(회전율 4.15)과 21세기북스(0.56)를 합치면 임프린트별 차이는 사라진다.
--   그래도 합치는 이유는 SEOJI 가 이 그룹을 '(주식회사)북21' 한 가지로만 보내오기 때문이다
--   (실측: 카탈로그 39권 전부 이 표기, 임프린트명 0건). 어느 임프린트인지 알 수 없는
--   후보에게 줄 수 있는 가장 정직한 값은 그룹 전체 평균이다.
--   나중에 SEOJI 가 임프린트명을 보내기 시작하면 해당 행을 지워 다시 나누면 된다.
--
-- 이 파일이 별칭 데이터의 단일 출처다. 새 별칭은 여기에 추가하고 파일째 다시 실행한다.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 0. norm_publisher 가 바뀌었으므로 생성열을 다시 계산시킨다.
--    생성열(stored)은 immutable 함수를 신뢰해 값을 저장해 둔다. 함수 본문만 바꾸면
--    기존 행의 publisher_key 는 옛 값 그대로 남는다(실측 9,873행 중 1,707행이 '(...' 로 시작).
--
--    함정: 아무 열이나 갱신한다고 다시 계산되지 않는다. 생성식이 참조하는 열이
--    update 대상 목록에 들어 있어야 한다. `set last_seen = last_seen` 은 1,707행을
--    그대로 통과시켰고, `set publisher = publisher` 로 바꾸고서야 계산됐다(실측).
--    열을 drop/add 하지 않는 이유: v_book_catalog_ko 가 bc.* 로 이 열에 의존한다.
--
--    (점수 뷰는 canon_publisher(bc.publisher) 를 즉석 계산하므로 점수 자체는 영향이 없고,
--     이 열은 인덱스·시리즈 키 용도다. 그래도 어긋난 채 두면 나중에 반드시 문다.)
-- ----------------------------------------------------------------------------

update public.book_catalog set publisher = publisher
 where publisher_key is distinct from public.norm_publisher(publisher);


-- ----------------------------------------------------------------------------
-- 1. 별칭 등재
--    alias_key / canonical_key 는 norm_publisher() 를 통과한 값이어야 한다.
--    그래서 원문 표기를 적고 함수로 감싼다 - 손으로 정규화한 문자열을 적지 말 것.
-- ----------------------------------------------------------------------------

delete from public.publisher_aliases;

-- 1-A. 미래엔 그룹
--      실측에서 세 표기가 각각 회전율 16.3 / 9.4 / 10.5 로 흩어져 있었다.
insert into public.publisher_aliases (alias_key, canonical_key, note) values
  (public.norm_publisher('미래엔아이세움'),   public.norm_publisher('아이세움'), '동일 임프린트'),
  (public.norm_publisher('Mirae N 아이세움'), public.norm_publisher('아이세움'), '동일 임프린트'),
  (public.norm_publisher('미래엔'),           public.norm_publisher('아이세움'), '동일 그룹 - 분리하려면 이 행 삭제')
on conflict (alias_key) do nothing;

-- 1-B. 북이십일 그룹
--      SEOJI 표기: '(주식회사)북21' 1종(카탈로그 39권).
--      소장 표기: 20종 893권, 대출 2,390건, 회전율 1.190 - 전체 평균 0.558의 2.1배.
--      묶기 전 '북21' 은 통계 행이 아예 없어 중립값(0.5 x 24 = 12점)을 받고 있었다.
--      ISBN 발행자기호 978-89-509 / 979-11-7661 / 979-11-711x 로 동일 등록 주체 확인.
insert into public.publisher_aliases (alias_key, canonical_key, note) values
  (public.norm_publisher('(주식회사)북21'),        public.norm_publisher('북이십일'), 'SEOJI 등록 법인명'),
  (public.norm_publisher('21세기북스'),            public.norm_publisher('북이십일'), '임프린트(성인 교양)'),
  (public.norm_publisher('아울북'),                public.norm_publisher('북이십일'), '임프린트(어린이)'),
  (public.norm_publisher('을파소'),                public.norm_publisher('북이십일'), '임프린트(어린이)'),
  (public.norm_publisher('아르테'),                public.norm_publisher('북이십일'), '임프린트(문학)'),
  (public.norm_publisher('arte'),                  public.norm_publisher('북이십일'), '아르테 로마자 표기'),
  (public.norm_publisher('아프테'),                public.norm_publisher('북이십일'), '아르테 오기'),
  (public.norm_publisher('Arte pop'),              public.norm_publisher('북이십일'), '아르테팝'),
  (public.norm_publisher('artenoir'),              public.norm_publisher('북이십일'), '아르테누아르'),
  (public.norm_publisher('레드리버'),              public.norm_publisher('북이십일'), '임프린트'),
  (public.norm_publisher('북이십일 21세기북스'),   public.norm_publisher('북이십일'), '모브랜드+임프린트 혼기'),
  (public.norm_publisher('북이십일 을파소'),       public.norm_publisher('북이십일'), '모브랜드+임프린트 혼기'),
  (public.norm_publisher('북이십일 아르테'),       public.norm_publisher('북이십일'), '모브랜드+임프린트 혼기'),
  (public.norm_publisher('북이십일 아울북'),       public.norm_publisher('북이십일'), '모브랜드+임프린트 혼기'),
  (public.norm_publisher('북이십일 레드리버'),     public.norm_publisher('북이십일'), '모브랜드+임프린트 혼기'),
  (public.norm_publisher('북이십일 arte'),         public.norm_publisher('북이십일'), '모브랜드+임프린트 혼기'),
  (public.norm_publisher('북이십일 19.0'),         public.norm_publisher('북이십일'), '임프린트'),
  (public.norm_publisher('북21세기북스'),          public.norm_publisher('북이십일'), '오기'),
  (public.norm_publisher('파주;21세기북스'),       public.norm_publisher('북이십일'), '발행지가 섞인 표기'),
  (public.norm_publisher('아르테 ; 북이십일'),     public.norm_publisher('북이십일'), '발행지가 섞인 표기')
on conflict (alias_key) do nothing;

-- 1-C. 디앤씨미디어 그룹
--      SEOJI 는 '(주)디앤씨미디어 L노벨' 처럼 법인명+임프린트로 보내고,
--      우리 장서는 'D&C Books' / 'B-Lab' 같은 임프린트 로마자 표기로 들어와 있다.
--      ISBN 979-11-278x 로 동일 등록 주체 확인. 규모는 작다(소장 약 70권).
--      '파피루스' 는 동명 출판사가 따로 있을 수 있어 일부러 넣지 않았다.
insert into public.publisher_aliases (alias_key, canonical_key, note) values
  (public.norm_publisher('(주)디앤씨미디어 L노벨'),      public.norm_publisher('디앤씨미디어'), 'SEOJI 표기'),
  (public.norm_publisher('(주)디앤씨미디어 파피루스'),   public.norm_publisher('디앤씨미디어'), 'SEOJI 표기'),
  (public.norm_publisher('(주)디앤씨미디어 디앤씨웹툰'), public.norm_publisher('디앤씨미디어'), 'SEOJI 표기'),
  (public.norm_publisher('디앤씨미디어 리드비'),         public.norm_publisher('디앤씨미디어'), 'SEOJI 표기'),
  (public.norm_publisher('D&C 미디어'),                  public.norm_publisher('디앤씨미디어'), '로마자 표기'),
  (public.norm_publisher('D&C Books'),                   public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('디앤씨북스'),                  public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('디앤씨books'),                 public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('B-Lab'),                       public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('B-Lap'),                       public.norm_publisher('디앤씨미디어'), '임프린트 오기'),
  (public.norm_publisher('D&C Webtoon'),                 public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('D&C Webtoon biz'),             public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('D&C weebtoonbiz'),             public.norm_publisher('디앤씨미디어'), '임프린트 오기'),
  (public.norm_publisher('디앤씨웹툰비즈'),              public.norm_publisher('디앤씨미디어'), '임프린트'),
  (public.norm_publisher('디앤씨'),                      public.norm_publisher('디앤씨미디어'), '축약 표기')
on conflict (alias_key) do nothing;

-- 1-D. 시대에듀 그룹 (구 시대고시기획)
--      후보는 대부분 수험서라 배제 규칙에서 걸러지지만, 남는 건 제대로 계산되게 둔다.
insert into public.publisher_aliases (alias_key, canonical_key, note) values
  (public.norm_publisher('(주)시대고시기획시대교육'), public.norm_publisher('시대에듀'), 'SEOJI 등록 법인명'),
  (public.norm_publisher('시대에듀 :시대고시기획'),   public.norm_publisher('시대에듀'), '부표제 혼기'),
  (public.norm_publisher('시대고시기획'),             public.norm_publisher('시대에듀'), '사명 변경 전'),
  (public.norm_publisher('시대인'),                   public.norm_publisher('시대에듀'), '임프린트(일반서)')
on conflict (alias_key) do nothing;

comment on table public.publisher_aliases is
  '출판사 이형 표기 별칭. norm_publisher() 로 흡수되지 않는 "이름 자체가 다른" 경우만 등재한다. '
  '단일 출처는 db/publisher_aliases.sql - 여기에 행을 추가하고 파일째 재실행할 것. '
  '직접 insert 하면 다음 실행의 delete 에서 사라진다.';


-- ----------------------------------------------------------------------------
-- 2. 통계 재계산
--    canon_publisher() 결과가 바뀌었으므로 출판사 통계를 다시 만들어야 한다.
-- ----------------------------------------------------------------------------

select public.refresh_acquisition_stats();


-- ============================================================================
-- 점검 쿼리 - 다음 별칭을 찾을 때 그대로 쓴다 (실행문 아님, 주석)
-- ============================================================================
--
-- 점검 1) 배제 규칙을 통과했는데 소장 이력이 안 붙는 출판사 (권수 순)
--   select vc.publisher, count(*) n
--     from public.v_candidate_scores vc
--    where not vc.excluded and not vc.already_owned
--      and public.acquisition_block_reason(vc.publisher, vc.title, vc.pre_price) is null
--      and coalesce(vc.pub_holdings, 0) = 0
--    group by 1 order by 2 desc limit 30;
--
-- 점검 2) 그 출판사의 ISBN 발행자기호가 소장측에 있는가 (같으면 이름만 다른 것)
--   select left(regexp_replace(bc.ea_isbn,'[^0-9]','','g'), 8) as pre,
--          count(*) as 후보권수,
--          (select string_agg(distinct b.publisher, ' / ')
--             from public.books b
--            where left(regexp_replace(coalesce(b.isbn,''),'[^0-9]','','g'), 8)
--                  = left(regexp_replace(bc.ea_isbn,'[^0-9]','','g'), 8)) as 소장측
--     from public.book_catalog bc
--    where bc.publisher = '여기에 출판사명'
--    group by 1 order by 2 desc;
--
--   * 8자리 절단은 발행자기호가 4~5자리인 출판사에서 남의 구간과 섞인다.
--     소장측에 여러 무관한 이름이 줄줄이 나오면 접두 충돌이니 별칭으로 넣지 말 것.
--
-- 점검 3) 등재 후 매칭률 확인
--   select count(*) 후보수,
--          count(*) filter (where coalesce(pub_holdings,0) > 0) 이력있음,
--          round(100.0 * count(*) filter (where coalesce(pub_holdings,0) > 0) / count(*), 1) pct
--     from public.v_candidate_scores
--    where not excluded and not already_owned;
-- ============================================================================
