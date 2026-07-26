// B-01 전용 — 주간 취합된 public.acquisition_candidates 후보 풀 조회 프록시.
// DB 비밀번호는 서버에만 두고, 브라우저에는 선정에 필요한 비민감 서지 필드만 반환한다.
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

  const requestedLimit = Number(req.query?.limit || 500);
  const limit = Math.min(Math.max(Number.isFinite(requestedLimit) ? requestedLimit : 500, 1), 1000);
  const startDate = String(req.query?.start_date || "").replace(/[^0-9]/g, "");
  const endDate = String(req.query?.end_date || "").replace(/[^0-9]/g, "");
  const values = [];
  const where = ["status = 'candidate'"];
  if (/^\d{8}$/.test(startDate)) {
    values.push(startDate);
    where.push(`regexp_replace(coalesce(pubdate, ''), '[^0-9]', '', 'g') >= $${values.length}`);
  }
  if (/^\d{8}$/.test(endDate)) {
    values.push(endDate);
    where.push(`regexp_replace(coalesce(pubdate, ''), '[^0-9]', '', 'g') <= $${values.length}`);
  }
  values.push(limit);

  try {
    const { rows } = await getPool().query(
      `select id, isbn, title, author, publisher, pubdate, price, form_detail,
              genre, sources, recommend_count, popnote, verified, first_seen, last_seen
         from public.acquisition_candidates
        where ${where.join(" and ")}
        order by recommend_count desc, verified desc,
                 regexp_replace(coalesce(pubdate, ''), '[^0-9]', '', 'g') desc,
                 last_seen desc
        limit $${values.length}`,
      values,
    );
    return res.status(200).json({ count: rows.length, candidates: rows });
  } catch (error) {
    return res.status(500).json({ error: error.message });
  }
};
