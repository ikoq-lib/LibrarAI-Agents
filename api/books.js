// B-03 복본 에이전트 전용 — Supabase public.books 실제 조회 프록시.
// pg(node-postgres)로 Supabase pooler에 직접 연결한다(서비스 롤 키 대신 기존 검증된 DB 비밀번호 재사용).
const { Pool } = require('pg');

const AUTHOR_NORMALIZE = "(지음|옮김|역|글\\.?|그림|저|편)\\.?|[;,·]";

let pool;
function getPool() {
  if (!pool) {
    pool = new Pool({
      host: 'aws-0-ap-southeast-1.pooler.supabase.com',
      port: 5432,
      user: 'postgres.tkyaganfdfiuesvbcbkr',
      password: process.env.SUPABASE_DB_PASSWORD,
      database: 'postgres',
      ssl: { rejectUnauthorized: false },
      max: 3,
    });
  }
  return pool;
}

async function checkOne(db, candidate) {
  const isbn = (candidate.isbn || '').trim();
  if (isbn) {
    const { rows } = await db.query(
      `select reg_no, title, author, call_no, room, material_status, loan_status
       from public.books where isbn = $1`,
      [isbn]
    );
    if (rows.length > 0) {
      return {
        candidate_id: candidate.candidate_id,
        match_type: 'duplicate',
        matched_isbn: isbn,
        matched_title: rows[0].title,
        existing_copies: rows.length,
        call_no: rows[0].call_no,
        status: 'confirmed',
      };
    }
  }

  const title = (candidate.title || '').trim();
  if (title) {
    const { rows } = await db.query(
      `select reg_no, title, author, isbn, call_no,
              similarity(title, $1) as title_sim,
              similarity(
                regexp_replace(coalesce(author, ''), '${AUTHOR_NORMALIZE}', ' ', 'g'),
                regexp_replace($2, '${AUTHOR_NORMALIZE}', ' ', 'g')
              ) as author_sim
       from public.books
       where title % $1
       order by title_sim desc
       limit 5`,
      [title, candidate.author || '']
    );
    if (rows.length > 0) {
      const top = rows[0];
      const combined = Number(top.title_sim) * 0.7 + Number(top.author_sim) * 0.3;
      // .claude/agents/b-03-duplicate-check.md 확정 규칙: 70~85% 안전마진 포함, >=0.70은 전부 needs_review
      const matchType = combined >= 0.70 ? 'needs_review' : 'new';
      return {
        candidate_id: candidate.candidate_id,
        match_type: matchType,
        matched_isbn: top.isbn,
        matched_title: top.title,
        similarity_score: Number(combined.toFixed(4)),
        call_no: top.call_no,
        status: matchType === 'needs_review' ? 'pending_librarian_review' : 'confirmed',
      };
    }
  }

  return { candidate_id: candidate.candidate_id, match_type: 'new', similarity_score: 0, status: 'confirmed' };
}

module.exports = async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });

  if (!process.env.SUPABASE_DB_PASSWORD) {
    return res.status(500).json({ error: 'SUPABASE_DB_PASSWORD가 서버에 설정되지 않았습니다.' });
  }

  const { action, candidates } = req.body || {};

  try {
    if (action === 'duplicate_check') {
      if (!Array.isArray(candidates) || candidates.length === 0) {
        return res.status(400).json({ error: 'candidates 배열이 필요합니다.' });
      }
      const db = getPool();
      const results = [];
      for (const c of candidates) {
        results.push(await checkOne(db, c));
      }
      return res.status(200).json({ results });
    }
    return res.status(400).json({ error: `알 수 없는 action: ${action}` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
