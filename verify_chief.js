// verify_chief.js — chief-coordinator 오케스트레이션 루프 결정론 검증 (v4 단일 접점)
//
// `page.route('**/api/chat')`로 요청 본문 내용에 따라 SSE 응답을 스텁하여, 실제 LLM 없이
// (레버4 병렬화로 콜 순서가 비결정적이므로 순번 대신 내용 매칭으로 라우팅)
// chief 1차(DISPATCH) → DM-01(ROUTE→리프) → DM-03(urgent escalation) → 집계 주입 →
// chief 2차(확인필요 미니 노트 + ①~⑤ 문서) 전체 사이클을 재현하고, 진행 패널·leafSteps·
// 미니 노트·⑤절 렌더와 집계 주입 요청 바디의 escalations JSON, 새로고침 복원/interrupted
// 강등까지 검증한다.
//
// 실행: NODE_PATH=".../node_modules" node verify_chief.js
const { chromium } = require('playwright');
const path = require('path');

const FILE_URL = 'file:///' + path.resolve(__dirname, 'LibrarAI.html').replace(/\\/g, '/');

// ── 호출 순번별 chief 응답 스텁 ──────────────────────────────────
// 모든 /api/chat 호출이 이 순서로 소비된다(디스패치 순차 실행이 결정론적이라 순번 고정):
//  1 chief 1차   → DISPATCH(DM-01, DM-03)
//  2 DM-01 1차   → ROUTE(b03-duplicate)
//  3 리프 b03    → 요약(사이드이펙트 없음)
//  4 DM-01 후속  → 도메인 최종 요약
//  5 DM-03       → 요약 + urgent ESCALATIONS
//  6 chief 2차   → ===확인필요=== 미니 노트 + ①~⑤ 통합 문서
const REPLIES = [
  // 1: chief 1차 — 위임 판단
  `관련 도메인 에이전트에 조회를 시작합니다.
===DISPATCH===
{"scope":"weekly","target_period":"2026-W30","targets":[{"agent":"dm01-collection-domain","instruction":"INSTR_DM01_주간장서계획조회"},{"agent":"dm03-reading-culture-domain","instruction":"INSTR_DM03_주간독서문화계획조회"}],"self_tasks":["주간통계작성"]}
===DISPATCH_END===`,
  // 2: DM-01 1차 — 리프 위임(ROUTE)
  `장서 도메인 하위 리프에 위임합니다.
===ROUTE===
{"targets":["b03-duplicate"],"note":"이번 주 복본 현황 확인"}
===ROUTE_END===`,
  // 3: 리프 b03 — 요약(DB_QUERY 블록 없음 → 추가 왕복 없음)
  `LEAFMARK_복본판정요약: 소장 3부 확인, 추가구입 불필요.`,
  // 4: DM-01 후속 — 도메인 최종 요약(escalation 없음)
  `DM01_최종요약: 주간 장서 도메인 계획 이상 없음. 정기수서 예정.`,
  // 5: DM-03 — 요약 + urgent escalation
  `DM03_최종요약: 독서동아리 3기 진행 예정.
===ESCALATIONS===
[{"item":"ESC_강사료_기준초과_승인필요","urgency":"urgent","source_leaf":"d-03"}]
===ESCALATIONS_END===`,
  // 6: chief 2차 — 확인필요 미니 노트 + ①~⑤ 통합 문서
  `===확인필요===
- 항목: ESC_강사료_기준초과_승인필요 (출처: DM-03 / D-03)
- 사유: 강사료가 회기당 기준 단가를 초과함
- 요청 판단: 초과 집행 승인 여부 결정 필요
===확인필요끝===

# 2026-W30 주간 업무 계획 (초안)

## ① 표지
작성: 기획업무팀 기획담당

## ② 요약
장서·독서문화 도메인 주간 계획 취합본입니다.

## ⑤ 확인·승인 필요 항목
- ESC_강사료_기준초과_승인필요 (DM-03)

_초안 · 최고관리자 검토 전 미확정_`,
];

// SSE 한 방에 content 전체 + [DONE] 전송 (requestApi가 \n 단위로 파싱)
const sse = (content) =>
  `data: ${JSON.stringify({ choices: [{ delta: { content } }] })}\n\n` +
  `data: [DONE]\n\n`;

const results = [];
const check = (name, cond) => { results.push({ name, pass: !!cond }); if (!cond) console.log('  ✗ FAIL:', name); else console.log('  ✓', name); };

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text().slice(0, 300)); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + String(e).slice(0, 300)));

  const requestBodies = [];
  let callIdx = 0;
  // 내용 기반 라우팅 — 병렬 실행이라 순번을 신뢰할 수 없으므로 요청 본문의 마커로 어떤 콜인지 판별한다.
  // 마커는 반드시 "요청 페이로드에만" 있고 시스템 프롬프트엔 없는 문구를 쓴다
  // (프롬프트에 [집계 결과]·[리프 산출물]·[chief-coordinator 요청] 문구가 들어있어 순진한 매칭은 충돌함).
  const pickReply = (b) => {
    if (b.includes('### escalations 취합')) return REPLIES[5];                          // chief 2차(집계 주입 고유 헤딩)
    if (b.includes('LEAFMARK')) return REPLIES[3];                                      // DM-01 후속(리프 산출물 원문 에코)
    if (b.includes('이번 주 복본 현황 확인')) return REPLIES[2];                          // 리프 b03(ROUTE note)
    if (b.includes('[chief-coordinator 요청]') && b.includes('INSTR_DM01')) return REPLIES[1]; // DM-01 1차(ROUTE)
    if (b.includes('[chief-coordinator 요청]') && b.includes('INSTR_DM03')) return REPLIES[4]; // DM-03
    return REPLIES[0];                                                                 // chief 1차(DISPATCH)
  };
  await page.route('**/api/chat', async (route) => {
    const body = route.request().postData() || '';
    requestBodies.push(body);
    callIdx++;
    await route.fulfill({
      status: 200,
      headers: { 'content-type': 'text/event-stream; charset=utf-8', 'cache-control': 'no-cache' },
      body: sse(pickReply(body)),
    });
  });

  await page.goto(FILE_URL);
  await page.waitForTimeout(2500);

  console.log('\n[1] 초기 홈 렌더');
  check('총괄 채팅 랜딩 노출', await page.locator('text=무엇을 처리할까요').count() >= 1);

  // ── 퀵 액션으로 주간 계획 지시 ──
  console.log('\n[2] "이번 주 업무 계획" 퀵 액션 실행');
  await page.getByRole('button', { name: '이번 주 업무 계획' }).click();

  // chief 1차 후 진행 패널 + 디스패치 카드 2개
  await page.waitForFunction(() => document.body.innerText.includes('실행 현황'), { timeout: 8000 }).catch(() => {});
  check('진행 패널(실행 현황) 렌더', await page.locator('text=실행 현황').count() >= 1);
  check('DM-01 디스패치 카드(instruction)', await page.locator('text=INSTR_DM01_주간장서계획조회').count() >= 1);
  check('DM-03 디스패치 카드(instruction)', await page.locator('text=INSTR_DM03_주간독서문화계획조회').count() >= 1);
  check('주간 계획 scope 라벨', await page.locator('text=주간 계획').count() >= 1);

  // 최종 문서까지 대기(6번째 호출 소비 = chief 2차)
  await page.waitForFunction(() => document.body.innerText.includes('확인·승인 필요 항목'), { timeout: 12000 }).catch(() => {});

  console.log('\n[3] leafSteps / escalation / 미니 노트 / 최종 문서');
  check('리프(b03) leafStep 요약 렌더', await page.locator('text=LEAFMARK_복본판정요약').count() >= 1);
  check('DM-03 urgent escalation 배지(⚠ 확인)', await page.locator('text=/⚠ 확인 1/').count() >= 1);
  check('확인 필요 미니 노트 카드', await page.locator('text=수시 미니 노트').count() >= 1);
  check('미니 노트 본문(escalation 인용)', await page.locator('text=ESC_강사료_기준초과_승인필요').count() >= 1);
  check('통합 문서 ⑤절 렌더', await page.locator('text=확인·승인 필요 항목').count() >= 1);
  check('run 완료 badge', await page.locator('text=완료').count() >= 1);

  console.log('\n[4] 집계 주입 요청 바디 검증');
  check('총 6회 /api/chat 호출', callIdx === 6);
  const aggBody = requestBodies.find(b => b.includes('### escalations 취합')) || '';
  check('집계 주입 바디에 escalations 취합 포함', aggBody.includes('escalations 취합'));
  check('집계 주입 바디에 urgent escalation JSON 포함', aggBody.includes('ESC_강사료_기준초과_승인필요') && aggBody.includes('urgent'));
  check('집계 주입 바디에 self_tasks(주간통계작성) 포함', aggBody.includes('주간통계작성'));

  console.log('\n[5] 새로고침 후 대화/실행 복원');
  await page.reload();
  await page.waitForTimeout(2000);
  check('복원: 진행 패널 유지', await page.locator('text=실행 현황').count() >= 1);
  check('복원: 최종 문서 ⑤절 유지', await page.locator('text=확인·승인 필요 항목').count() >= 1);

  console.log('\n[6] interrupted 강등 (진행 중 run 새로고침)');
  await page.evaluate(() => {
    const st = {
      chiefMsgs: [
        { role: 'assistant', content: '안녕하세요! 업무 총괄 에이전트입니다.' },
        { role: 'user', content: 'INTERRUPT_TEST 지시' },
        { role: 'assistant', kind: 'execution', runId: 'run_interrupt', content: '' },
      ],
      chiefRuns: {
        run_interrupt: {
          status: 'running', scope: 'weekly', target_period: '2026-W30', event_name: null,
          self_tasks: [], startedAt: new Date().toISOString(),
          dispatches: [{ agent: 'dm01-collection-domain', instruction: 'INTERRUPT_DISPATCH', status: 'running', resultText: '', escalations: [], leafSteps: [] }],
        },
      },
    };
    localStorage.setItem('librarai_chief_state', JSON.stringify(st));
  });
  await page.reload();
  await page.waitForTimeout(2000);
  check('interrupted: "새로고침으로 중단" badge', await page.locator('text=새로고침으로 중단').count() >= 1);
  check('interrupted: 진행 중이던 dispatch가 error로 강등', await page.locator('text=/실패/').count() >= 1);

  console.log('\n[콘솔 오류]', errors.length ? errors.join('\n---\n') : '(없음)');
  check('페이지/콘솔 오류 없음', errors.length === 0);

  const failed = results.filter(r => !r.pass);
  await browser.close();
  console.log(`\n=== ${failed.length === 0 ? 'PASS' : 'FAIL'} (${results.length - failed.length}/${results.length}) ===`);
  process.exit(failed.length === 0 ? 0 : 1);
})();
