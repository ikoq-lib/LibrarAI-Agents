// B-02 전용 — 희망도서 주간 신청 건 조회 프록시.
// DB 비밀번호는 서버에만 두고, 브라우저에는 판정에 필요한 필드만 내려보낸다.
//
// 신청자 이름은 원문 그대로 내보내지 않는다. wishlist_requests 는 지금은 전량 목업
// (테스트N)이지만 나중에 실제 신청이 적재될 자리이므로, 실명은 마스킹해서 라벨로만
// 준다. B-02 의 FN-04(1인 월 3권 한도)는 이름이 아니라 patron_id 로 집계하면 된다.
//
//   mode=week  (기본) : 처리 대상 주차 한 주. week=YYYY-MM-DD(월요일)로 지정하고,
//                       비우면 아직 처리되지 않은 건이 남은 가장 최근 주차를 고른다.
//   mode=month        : month=YYYY-MM 한 달치. FN-07 월간 신청 현황용.
//   mode=summary      : 주차별 집계만(v_wishlist_weekly). 목록 없이 추이만 볼 때.
//
// 각 행에는 그 신청자의 "해당 월 누적 신청 권수"(month_count)를 함께 실어 보낸다.
// B-02 가 한도 초과를 판정하려면 이번 주 목록만으로는 부족하고 월 누계가 필요하다.
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

// 실명은 성만 남기고 가린다. 목업(테스트N)은 식별정보가 아니므로 그대로 둔다.
// 사서가 화면에서 신청자를 구분할 수 있어야 하므로 patron_id 를 함께 준다.
const PATRON_LABEL = `
  case when p.is_mock then p.name
       when length(p.name) <= 1 then p.name
       else left(p.name, 1) || repeat('*', length(p.name) - 1)
  end`;

// 신청자별 월 누계. FN-04 한도 판정의 분모다.
// 반려 확정 건도 센다 — 한도는 신청 시점 기준이라는 것이 규정이다.
//
// 윈도 함수(count(*) over (partition by patron_id, 월))로 쓰면 안 된다. 윈도는 where 로
// 걸러진 뒤의 행에서만 계산되므로, 주차 조회에서는 "그 주 안에서의 건수"가 나와 월 3권
// 초과를 영영 못 잡는다(2026-09-12 실측: 9월 4권 신청자 3명이 전부 1로 보였다).
// 그래서 전체 테이블을 보는 상관 서브쿼리로 센다.
//
// 월 경계는 KST 로 끊는다. timestamptz 에 date_trunc 를 그냥 쓰면 세션 TimeZone 에 따라
// 답이 달라져, 월초·월말 자정 근처 신청이 접속 환경마다 다른 달로 잡힌다.
const MONTH_COUNT = `
  (select count(*) from public.wishlist_requests r2
    where r2.patron_id = r.patron_id
      and date_trunc('month', r2.requested_at at time zone 'Asia/Seoul')
        = date_trunc('month', r.requested_at at time zone 'Asia/Seoul'))::int`;

const ROW_COLUMNS = `
  r.id,
  to_char(r.request_week, 'YYYY-MM-DD')            as request_week,
  to_char(r.requested_at at time zone 'Asia/Seoul', 'YYYY-MM-DD HH24:MI') as requested_at,
  r.patron_id,
  ${PATRON_LABEL}                                  as patron_label,
  p.age,
  p.age_group,
  p.gender,
  r.ea_isbn                                        as isbn,
  r.title,
  r.author,
  r.publisher,
  r.pre_price                                      as price,
  r.form_detail,
  r.source,
  r.status,
  r.reject_reason,
  ${MONTH_COUNT}                                   as month_count,
  bc.ea_add_code                                   as isbn_add_code,
  bc.add_code_audience,
  bc.add_code_form,
  bc.add_code_subject,
  to_char(bc.publish_predate, 'YYYYMMDD')          as pubdate,
  bc.series_title,
  -- form_detail 이 book_catalog(SEOJI 수집분)에서 온 값이면 B-02 가 R-04 를 판정할 때
  -- SEOJI 를 다시 조회할 필요가 없다. 출처가 확실한 건에만 true 를 준다.
  (bc.ea_isbn is not null and r.form_detail is not null) as format_verified`;

const FROM = `
  from public.wishlist_requests r
  join public.wishlist_patrons p on p.id = r.patron_id
  left join public.book_catalog bc on bc.ea_isbn = r.ea_isbn`;

/** 처리할 주차. 지정이 없으면 미처리 건이 남은 가장 최근 주차를 고른다. */
async function resolveWeek(raw) {
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(raw || ""))) return raw;
  const { rows } = await getPool().query(
    `select to_char(request_week, 'YYYY-MM-DD') as w
       from public.wishlist_requests
      where status = 'pending'
      order by request_week desc
      limit 1`,
  );
  if (rows[0]?.w) return rows[0].w;
  // 미처리가 없으면 가장 최근 주차를 보여준다(이미 처리한 주차 조회).
  const last = await getPool().query(
    `select to_char(max(request_week), 'YYYY-MM-DD') as w from public.wishlist_requests`,
  );
  return last.rows[0]?.w || null;
}

async function queryWeek(query) {
  const week = await resolveWeek(query?.week);
  if (!week) return { week: null, rows: [] };
  const { rows } = await getPool().query(
    `select ${ROW_COLUMNS} ${FROM}
      where r.request_week = $1::date
      order by r.requested_at, r.id`,
    [week],
  );
  return { week, rows };
}

async function queryMonth(query) {
  const month = /^\d{4}-\d{2}$/.test(String(query?.month || ""))
    ? `${query.month}-01`
    : null;
  const { rows } = await getPool().query(
    `select ${ROW_COLUMNS} ${FROM}
      where date_trunc('month', r.requested_at at time zone 'Asia/Seoul')
            = date_trunc('month', coalesce($1::date, current_date))
      order by r.requested_at, r.id`,
    [month],
  );
  return { month: month ? month.slice(0, 7) : null, rows };
}

async function querySummary() {
  const { rows } = await getPool().query(
    `select to_char(request_week, 'YYYY-MM-DD') as request_week,
            "신청건수" as requested, "신청자수" as patrons,
            "구입대상" as approved, "반려" as rejected,
            "수동검토" as manual_review, "미처리" as pending,
            "구입예정액" as planned_amount
       from public.v_wishlist_weekly
      order by request_week desc
      limit 26`,
  );
  return { rows };
}

module.exports = async function handler(req, res) {
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Access-Control-Allow-Methods", "GET, OPTIONS");
  res.setHeader("Access-Control-Allow-Headers", "Content-Type");
  // 주 1회만 바뀌는 데이터지만, 사서가 처리 상태를 바꾸면 바로 보여야 하므로 짧게 잡는다.
  res.setHeader("Cache-Control", "public, s-maxage=60, stale-while-revalidate=300");

  if (req.method === "OPTIONS") return res.status(200).end();
  if (req.method !== "GET") return res.status(405).json({ error: "Method not allowed" });
  if (!process.env.SUPABASE_DB_PASSWORD) {
    return res.status(500).json({ error: "SUPABASE_DB_PASSWORD가 서버에 설정되지 않았습니다." });
  }

  const mode = String(req.query?.mode || "week").toLowerCase();
  const runners = { week: queryWeek, month: queryMonth, summary: querySummary };
  const run = runners[mode];
  if (!run) {
    return res.status(400).json({ error: `mode는 week·month·summary 중 하나여야 합니다: ${mode}` });
  }

  try {
    const out = await run(req.query || {});
    return res.status(200).json({ mode, count: out.rows.length, ...out, requests: out.rows });
  } catch (error) {
    // 42P01 = 테이블/뷰 없음. 스키마가 아직 적용되지 않은 배포 구간에서는 빈 목록으로 답한다
    // (B-02 탭 전체가 오류로 막히는 것보다, 신청 건이 없다고 알리는 편이 낫다).
    if (error.code === "42P01") {
      return res.status(200).json({
        mode, count: 0, requests: [], rows: [],
        warning: "희망도서 테이블이 아직 없습니다. db/wishlist_requests.sql 을 적용하세요.",
      });
    }
    return res.status(500).json({ error: error.message });
  }
};
