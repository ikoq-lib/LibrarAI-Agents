-- 추천도서 취합 에이전트가 주간 적재하는 "구입 후보 풀" 테이블.
-- 도서관 전체 소장 목록(public.books)과는 별개로 유지되며, 구매 확정 시 books로 승격한다.
-- 2026-07-26 생성.
create table if not exists public.acquisition_candidates (
  id            bigint generated always as identity primary key,
  dedup_key     text not null unique,          -- 중복 병합 키: ISBN 있으면 ISBN, 없으면 정규화(제목|저자)
  isbn          text,                           -- ISBN13 (SEOJI 검증 후 채움, 없을 수 있음)
  title         text not null,
  author        text,
  publisher     text,
  pubdate       text,                           -- YYYYMMDD 또는 원문
  price         integer,                        -- 정가(원)
  form_detail   text,                           -- 제본형태(SEOJI: 무선제본/양장본/보드북 등)
  genre         text,                           -- 발굴 분야/장르
  sources       text[] not null default '{}',   -- 추천 출처들(교보/예스24/이동진파이아키아/박곰희TV/국중 등)
  recommend_count integer not null default 1,   -- 추천 소스 수 = 인기 강도 신호
  popnote       text,                           -- 인기근거 요약
  verified      boolean not null default false, -- SEOJI 실존 검증 여부
  status        text not null default 'candidate', -- candidate | selected | purchased | rejected
  first_seen    timestamptz not null default now(),
  last_seen     timestamptz not null default now(),
  metadata      jsonb not null default '{}'::jsonb
);

create index if not exists acq_cand_status_idx  on public.acquisition_candidates (status);
create index if not exists acq_cand_pubdate_idx on public.acquisition_candidates (pubdate);
create index if not exists acq_cand_verified_idx on public.acquisition_candidates (verified);
create unique index if not exists acq_cand_isbn_uidx on public.acquisition_candidates (isbn) where isbn is not null;

-- RLS: 공개 읽기(웹앱 anon), 쓰기는 service_role(취합 스크립트)만 — 정책 없으므로 anon insert/update 차단됨.
alter table public.acquisition_candidates enable row level security;
drop policy if exists "acq_cand public read" on public.acquisition_candidates;
create policy "acq_cand public read" on public.acquisition_candidates for select using (true);
