// B-01 전용 — 수서 후보 조회 프록시.
// DB 비밀번호는 서버에만 두고, 브라우저에는 선정에 필요한 비민감 서지·점수 필드만 반환한다.
//
// 2026-08-27 전환: 1차 소스가 주간 취합 acquisition_candidates 에서
//   SEOJI 일일 전량 수집(book_catalog) + 5축 점수(v_candidate_scores) 로 바뀌었다.
//
//   mode=shortlist (기본) : acquisition_shortlist_kdc(n) — 배제 규칙·시리즈 상한·
//                           KDC 권수 쿼터·점수순 선정까지 끝난 최종 목록. 정기수서용.
//   mode=pool             : v_candidate_scores 점수순 상위 N — 훑어보기·수동 검토용.
//   mode=weekly           : 구 acquisition_candidates. 새 경로 장애 시 예비.
//
// 필드명은 프런트엔드 매퍼가 그대로 동작하도록 구 스키마 이름으로 별칭을 준다
// (ea_isbn→isbn, publish_predate→pubdate, pre_price→price). 점수 필드는 추가분이다.
const { Pool } = require("pg");

let pool;
function getPool() {
  if (!pool) {
    pool = new Pool({
      host: "aws-0-ap-southeast-1.pooler.supabase.com",
      port: 5432,
      user: "postgres.tkyaganfdfiuesvbcbkr",
      password: process.env.SUPABASE_DB_PASSWORD,
      database: "postgres",
      ssl: { rejectUnauthorized: false },
      max: 3,
    });
  }
  return pool;
}

// v_candidate_scores / acquisition_shortlist_kdc 공통 반환 열.
// 구 스키마 이름으로 별칭을 주어 프런트엔드 매퍼를 그대로 쓴다.
// add_code_form(발행형태 1자리)만 뷰에 없고 라벨(형태)로만 노출된다. book_catalog 를 조인해 원본 코드도 함께 준다.
const SCORED_COLUMNS = `
  s.ea_isbn                        as isbn,
  s.ea_add_code                    as isbn_add_code,
  s.add_code_audience,
  bc.add_code_form,
  s.add_code_subject,
  s.title, s.author, s.publisher,
  to_char(s.publish_predate, 'YYYYMMDD') as pubdate,
  s.pre_price                      as price,
  s.form_detail,
  s."주제"                          as genre,
  s."대상"                          as audience_label,
  s."대상구분"                       as audience_group,
  s."형태"                          as form_label,
  bc.series_title,
  s.already_owned,
  s.recommend_count,
  round(s.score_total, 1)      as score_total,
  round(s.score_publisher, 1)  as score_publisher,
  round(s.score_author, 1)     as score_author,
  round(s.score_pubdate, 1)    as score_pubdate,
  round(s.score_kdc, 1)        as score_kdc,
  round(s.score_price, 1)      as score_price,
  s.unknown_axes,
  s.pub_holdings, round(s.pub_turnover, 3) as pub_turnover,
  s.aut_holdings, round(s.aut_turnover, 3) as aut_turnover,
  true as verified`;

async function queryShortlist(query) {
  const n = clampInt(query?.n ?? query?.limit, 100, 1, 2000);
  const months = clampInt(query?.months, 15, 0, 60);
  const seriesMax = query?.series_max == null ? null : clampInt(query.series_max, 3, 1, 50);
  const { rows } = await getPool().query(
    `select ${SCORED_COLUMNS}
       from public.acquisition_shortlist_kdc($1, $2, $3) s
       join public.book_catalog bc on bc.ea_isbn = s.ea_isbn
      order by s.score_total desc, s.publish_predate desc`,
    [n, months, seriesMax],
  );
  return rows;
}

async function queryPool(query) {
  const limit = clampInt(query?.limit, 500, 1, 1000);
  const values = [];
  const where = ["not s.excluded", "not s.already_owned",
                 "public.acquisition_block_reason(s.publisher, s.title, s.pre_price) is null"];
  const startDate = digits(query?.start_date);
  const endDate = digits(query?.end_date);
  if (/^\d{8}$/.test(startDate)) {
    values.push(startDate);
    where.push(`to_char(s.publish_predate, 'YYYYMMDD') >= $${values.length}`);
  }
  if (/^\d{8}$/.test(endDate)) {
    values.push(endDate);
    where.push(`to_char(s.publish_predate, 'YYYYMMDD') <= $${values.length}`);
  }
  values.push(limit);
  const { rows } = await getPool().query(
    `select ${SCORED_COLUMNS}
       from public.v_candidate_scores s
       join public.book_catalog bc on bc.ea_isbn = s.ea_isbn
      where ${where.join(" and ")}
      order by s.score_total desc, s.publish_predate desc
      limit $${values.length}`,
    values,
  );
  return rows;
}

// 구 경로. 새 경로가 아직 배포되지 않았거나 장애일 때만 쓴다.
async function queryWeekly(query) {
  const limit = clampInt(query?.limit, 500, 1, 1000);
  const values = [];
  const where = ["status = 'candidate'"];
  const startDate = digits(query?.start_date);
  const endDate = digits(query?.end_date);
  if (/^\d{8}$/.test(startDate)) {
    values.push(startDate);
    where.push(`regexp_replace(coalesce(pubdate, ''), '[^0-9]', '', 'g') >= $${values.length}`);
  }
  if (/^\d{8}$/.test(endDate)) {
    values.push(endDate);
    where.push(`regexp_replace(coalesce(pubdate, ''), '[^0-9]', '', 'g') <= $${values.length}`);
  }
  values.push(limit);
  // acquisition_candidates 에는 부가기호 열이 없다(2026-08-27 확인). 열을 추가하는
  // 마이그레이션이 나중에 적용될 수 있으므로 있으면 쓰고 없으면 null 로 폴백한다.
  const tail = `title, author, publisher, pubdate, price, form_detail,
            genre, sources, recommend_count, popnote, verified, first_seen, last_seen,
            metadata->>'candidate_type' as candidate_type,
            metadata->>'usage_period' as usage_period,
            metadata->>'loan_count' as loan_count,
            metadata->>'reservation_count' as reservation_count,
            metadata->>'interlibrary_received_count' as interlibrary_received_count
       from public.acquisition_candidates
      where ${where.join(" and ")}
      order by recommend_count desc, verified desc,
               regexp_replace(coalesce(pubdate, ''), '[^0-9]', '', 'g') desc,
               last_seen desc
      limit $${values.length}`;
  try {
    const { rows } = await getPool().query(
      `select id, isbn, isbn_add_code, add_code_audience, add_code_form, add_code_subject, ${tail}`,
      values,
    );
    return rows;
  } catch (error) {
    if (error.code !== "42703") throw error;
    const { rows } = await getPool().query(
      `select id, isbn, null::text as isbn_add_code, null::text as add_code_audience,
              null::text as add_code_form, null::text as add_code_subject, ${tail}`,
      values,
    );
    return rows;
  }
}

function clampInt(raw, fallback, min, max) {
  const n = Number(raw);
  if (!Number.isFinite(n)) return fallback;
  return Math.min(Math.max(Math.trunc(n), min), max);
}

function digits(raw) {
  return String(raw || "").replace(/[^0-9]/g, "");
}

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  res.setHeader("Cache-Control", "public, s-maxage=300, stale-while-revalidate=600");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "GET") return res.status(405).json({ error: "Method not allowed" });
  if (!process.env.SUPABASE_DB_PASSWORD) {
    return res.status(500).json({ error: "SUPABASE_DB_PASSWORD가 서버에 설정되지 않았습니다." });
  }

  const mode = String(req.query?.mode || "shortlist").toLowerCase();
  const runners = { shortlist: queryShortlist, pool: queryPool, weekly: queryWeekly };
  const run = runners[mode];
  if (!run) {
    return res.status(400).json({ error: `mode는 shortlist·pool·weekly 중 하나여야 합니다: ${mode}` });
  }

  try {
    const rows = await run(req.query || {});
    return res.status(200).json({ mode, count: rows.length, candidates: rows });
  } catch (error) {
    // 새 스키마가 아직 배포되지 않은 구간에서는 구 경로로 자동 폴백한다.
    // 42P01 = 테이블/뷰 없음, 42883 = 함수 없음, 42703 = 열 없음.
    if (mode !== "weekly" && ["42P01", "42883", "42703"].includes(error.code)) {
      try {
        const rows = await queryWeekly(req.query || {});
        return res.status(200).json({
          mode: "weekly",
          fallback_from: mode,
          fallback_reason: error.message,
          count: rows.length,
          candidates: rows,
        });
      } catch (fallbackError) {
        return res.status(500).json({ error: fallbackError.message });
      }
    }
    return res.status(500).json({ error: error.message });
  }
};
