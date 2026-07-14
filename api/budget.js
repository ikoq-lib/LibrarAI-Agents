// A-03 예산관리 에이전트 전용 — Supabase public.budget_lines/budget_resolutions 실제 조회·기록 프록시.
// pg(node-postgres)로 Supabase pooler에 직접 연결한다(api/books.js와 동일하게 SUPABASE_DB_PASSWORD 재사용).
const { Pool } = require('pg');

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

async function getSnapshot(db) {
  const { rows } = await db.query(
    `select unique_key, unit_task, budget_kind, budget_mok, item1, item2, item3, item4, cost_code,
            budget_amount, executed_amount, planned_amount,
            (budget_amount - executed_amount) as balance,
            (budget_amount - executed_amount - planned_amount) as planned_balance
     from public.budget_lines
     order by unit_task, item1, item2, item3, item4`
  );
  return rows;
}

async function executeLine(db, { unique_key, amount, description, date, source }) {
  if (!unique_key || !amount || !description) {
    return { error: 'unique_key, amount, description는 필수입니다.' };
  }
  const amt = Math.round(Number(amount));
  if (!Number.isFinite(amt) || amt <= 0) {
    return { error: `금액이 올바르지 않습니다: ${amount}` };
  }
  const resolvedDate = date || new Date().toISOString().slice(0, 10);
  const month = `${parseInt(resolvedDate.slice(5, 7), 10)}월`;

  const client = await db.connect();
  try {
    await client.query('BEGIN');
    const { rows } = await client.query(
      `select unique_key, unit_task, item1, item2, item3, item4, budget_amount, executed_amount
       from public.budget_lines where unique_key = $1 for update`,
      [unique_key]
    );
    if (rows.length === 0) {
      await client.query('ROLLBACK');
      return { error: `budget_lines에 없는 고유값입니다(임의 생성 불가): ${unique_key}` };
    }
    const line = rows[0];
    const balance = Number(line.budget_amount) - Number(line.executed_amount);
    if (amt > balance) {
      await client.query('ROLLBACK');
      return {
        error: '예산 부족',
        unique_key,
        requested: amt,
        balance,
        line_label: [line.unit_task, line.item1, line.item2, line.item3, line.item4].filter(Boolean).join(' > '),
      };
    }
    await client.query(
      `insert into public.budget_resolutions (unique_key, resolved_date, resolved_month, description, amount, source)
       values ($1, $2, $3, $4, $5, $6)`,
      [unique_key, resolvedDate, month, description, amt, source || 'a03-web']
    );
    await client.query(
      `update public.budget_lines set executed_amount = executed_amount + $1, updated_at = now() where unique_key = $2`,
      [amt, unique_key]
    );
    await client.query('COMMIT');
    const newBalance = balance - amt;
    return {
      unique_key,
      line_label: [line.unit_task, line.item1, line.item2, line.item3, line.item4].filter(Boolean).join(' > '),
      amount: amt,
      balance_before: balance,
      balance_after: newBalance,
      resolved_date: resolvedDate,
      status: 'executed',
    };
  } catch (err) {
    await client.query('ROLLBACK').catch(() => {});
    throw err;
  } finally {
    client.release();
  }
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

  const { action, items, unique_key, amount, description, date, source } = req.body || {};

  try {
    const db = getPool();
    if (action === 'snapshot') {
      const rows = await getSnapshot(db);
      return res.status(200).json({ lines: rows });
    }
    if (action === 'execute') {
      // items: [{unique_key, amount, description, date}] 배치 처리 지원. 단건은 최상위 필드로도 받는다.
      const batch = Array.isArray(items) && items.length > 0
        ? items
        : [{ unique_key, amount, description, date }];
      const results = [];
      for (const item of batch) {
        results.push(await executeLine(db, { ...item, source }));
      }
      return res.status(200).json({ results });
    }
    return res.status(400).json({ error: `알 수 없는 action: ${action}` });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
};
