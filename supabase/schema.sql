-- LibrarAI 장서 DB 스키마
-- 소스: References/whole_book_list.xlsx (Sheet2, 73,390행)
-- 그레인: 1행 = 실물 소장 1부(등록번호 단위). 같은 서지(제어번호/ISBN)를 여러 부 소장하는 경우
--         복본으로 별도 행이 존재함 (예: 제어번호 최대 40건 중복, ISBN 최대 40건 중복).

create extension if not exists pg_trgm;

create table if not exists public.books (
  reg_no            text primary key,           -- 등록번호 (예: EM19289)
  title             text not null,               -- 서명
  author            text,                        -- 저자
  publisher         text,                        -- 출판사
  pub_year          smallint,                    -- 출판년 (원본 오기 값 존재, 아래 데이터 품질 노트 참고)
  loc_mark          text,                        -- 별치기호 (유/J/BIG/JBIG/소리책/JW/R/U)
  call_no           text,                        -- 청구기호 (KDC 분류기호 + 저자기호 + 권차)
  vol               text,                        -- 권ㆍ연차
  dup_no            smallint,                    -- 복본 번호 (NULL이면 사실상 1번째 부)
  room              text not null,               -- 자료실 (종합자료실/어린이자료실/종합실(신간도서)/어린이실(신간도서))
  shelf             text,                        -- 서가 (현재 원본에 값 없음, 향후 확장 대비)
  material_status   text not null,               -- 자료상태 (이용가능/정리중/소재불명/폐기제적/파손/대출불가(별치))
  loan_status       text not null,               -- 대출상태 (대출가능/대출중/상호대차 처리중/희망도서 대출대기/예약서가비치)
  is_blind          boolean not null default false,       -- Blind (열람/검색 제외 여부)
  is_biblio_blind   boolean not null default false,       -- 서지Blind
  ctrl_no           integer not null,            -- 제어번호 (서지 레코드 식별자, 복본 간 공유됨)
  isbn              text,                        -- ISBN (10/13자리, 극소수 원본 오기 존재)
  price             integer,                     -- 정리가격 (원)
  updated_at        timestamptz not null default now()
);

comment on table public.books is 'whole_book_list.xlsx 기반 장서 원부. 등록번호(실물 1부) 단위 그레인.';

create index if not exists books_isbn_idx on public.books (isbn);
create index if not exists books_ctrl_no_idx on public.books (ctrl_no);
create index if not exists books_room_idx on public.books (room);
create index if not exists books_call_no_idx on public.books (call_no);
create index if not exists books_title_trgm_idx on public.books using gin (title gin_trgm_ops);
create index if not exists books_author_trgm_idx on public.books using gin (author gin_trgm_ops);

-- title_trgm_idx / author_trgm_idx: B-03 복본판정 에이전트의 "제목+저자 유사도 ≥80%" 퍼지매치에 사용
-- (pg_trgm의 similarity()/% 연산자 활용)
