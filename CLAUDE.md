# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LibrarAI is a Korean public library AI management system. The three agents below are the original framing; the current implementation has grown into the v4 structure (chief-coordinator 단일 접점 + 6개 도메인 + 리프 에이전트 29개, `.claude/agents/`) — 이 절은 아직 갱신되지 않았다. 응답 LLM은 사이드바에서 교체 가능하므로 특정 벤더에 고정되어 있지 않다(아래 "Tech Stack" 참고).

- **평생학습 에이전트 (Lifelong Learning Agent)** — manages library program lifecycle: course planning, instructor hiring, student recruitment, attendance, and reporting across 7 workflow stages
- **수서 에이전트 (Acquisition Agent)** — manages book purchasing workflow using the Aladin Open API; handles 정기도서수서 (regular acquisitions) and 희망도서수서 (patron requests), including duplicate checking (ISBN, title, author)
- **이용자 응대 에이전트 (User Service Agent)** — kiosk-style patron-facing agent with voice + touch input; handles location guidance, loan/return/renewal, program info, and material recommendations

## Tech Stack

- **Frontend**: React (JSX), deployed on Vercel
- **Database**: Supabase (book DB, loan history, statistics)
- **AI**: OpenRouter (`LibrarAI.html`의 실제 백엔드). 이전에는 Groq(Llama 3.3)였음. `api/chat.js`는 `req.body`를 그대로 OpenRouter에 넘기는 순수 프록시라 **모델은 전적으로 클라이언트가 결정한다.**
  - **기본 모델: `qwen/qwen3.7-plus`** (2026-07-23 전환, 직전 기본값은 `anthropic/claude-sonnet-5`). 1M 컨텍스트, 100만 토큰당 입력 $0.32 / 출력 $1.28 — Sonnet 5 대비 입력 1/6·출력 1/8 가격. 단, 프롬프트가 256K 토큰을 넘으면 3배 요율($0.96/$3.84) 구간이 적용된다.
  - 선택 가능한 모델은 `LibrarAI.html`의 `CHAT_MODELS` 배열(6종)에 정의하고, 사이드바 하단 드롭다운에서 고른다. 선택값은 `localStorage["librarai_chat_model"]`에 유지되며, 저장값이 목록에 없으면 기본값으로 폴백한다.
  - **`CHAT_MODELS`에 추가하는 모델은 반드시 도구 호출(tools)을 지원해야 한다** — chief-coordinator의 리프 위임(ROUTE)이 도구 호출에 의존한다. 추가 전 `https://openrouter.ai/api/v1/models`(인증 불필요)에서 ID·`supported_parameters`·가격을 확인할 것. 모델 ID를 추측해서 넣지 말 것.
  - **실제 배포 시점에는 프롬프트 캐싱 비용 이점을 위해 Anthropic/OpenAI 다이렉트 API로 전환 예정** (아래 "Pending Issues" 참고)
- **External APIs**: Aladin Open API 차단으로 2026-07-09부터 SEOJI(국립중앙도서관 서지정보유통지원시스템)+네이버 책 검색 API로 대체 (`.env.local` 참고). **2026-07-15부터 Claude Code 에이전트(B-01·B-02)는 네이버 책 검색 API를 `mcp__naver-shopping__search-book` MCP 도구로 호출** (`~/.claude/mcp-servers/naver-api-mcp`, D-02가 쓰는 `search-shopping`과 동일 서버). 웹앱(`api/`)에서의 실제 호출 경로는 별도 확인 필요.
- **File processing**: xlsx.js (loaded dynamically from CDN) for KDC statistics Excel files

## Architecture Pattern

**`LibrarAI.html`(현재 메인 구현)의 실제 아키텍처(2026-07-09 확인):** 아래 항목들과 달리, 모든 ~30개 에이전트 탭이 **단일 공유 백엔드 프록시**(`api/chat.js`, Vercel 서버리스 함수)를 통해서만 API를 호출한다. API 키는 서버측 환경변수(`OPENROUTER_API_KEY`)에만 존재하며, **사이드바에 API 키를 입력하는 UI는 존재하지 않는다.** 브라우저에서 외부 LLM API를 직접 호출하는 코드도 없다. 사이드바 하단의 **응답 모델 드롭다운은 2026-07-23에 추가**된 것으로, API 키가 아니라 OpenRouter 모델 ID만 고른다(위 "Tech Stack" 참고).

아래는 원래(레퍼런스 구현 기준) 문서화된 패턴이며, 개별 에이전트 프로토타입 파일(`../library/*.jsx.txt`)에는 여전히 해당될 수 있으나 `LibrarAI.html`에는 적용되지 않는다:
- A hardcoded `SYSTEM_PROMPT` defining role, institution config, and workflow rules
- A `STAGES` array mapping workflow steps to sub-tasks and initial prompts
- A left sidebar for stage navigation and API key / file upload inputs
- A chat interface calling the Anthropic API directly from the browser
- Document output using delimiters (`===기안문시작===` / `===기안문끝===`, `===첨부시작===` / `===첨부끝===`) for official documents (기안문 + 첨부)

The reference implementation for the Lifelong Learning Agent is at `../library/lifelong-learning-agent_1.jsx.txt`.

## Key Domain Context

- **KDC**: Korean Decimal Classification — used for collection statistics and filtering
- **복본조사**: Duplicate check by ISBN (exact match = 복본), title+author ≥80% match = "상세조사 필요"
- **수서 기준**: Patron book requests have eligibility rules (3 books/person/month max; excludes out-of-print, foreign, e-books, 5+ year-old titles, high-cost >₩50,000, etc.)
- **예산**: Annual budget ₩100M total; lifelong learning sub-budget: instructor fees ₩15M, supplies ₩3M; instructor rate ₩100,000/session (₩50,000/hr × 2hrs)
- **강의실**: Room 1 (20 pax, adults), Rooms 2-3 (10 pax each, children)
- **문서**: Public institution document format — 기안문 (draft memo) + 첨부 (attachment) must be output as separate sections

## Environment Variables

Stored in `../.env.local` (parent directory):
- `ANTHROPIC_API_KEY` or similar — Claude API key
- Supabase URL + anon key
- Aladin TTB key (also configurable via sidebar UI in agent components)

## Document Output Format

- **모든 문서는 hwpx 형식으로 출력한다.** 행사 기획안, 기안문, 첨부 등 도서관 업무 관련 문서를 생성할 때는 항상 hwpx 파일로 만들어야 한다.
- hwpx 변환은 `hwpx-autofill-conversion` 스킬을 사용한다.

## 공문서 작성 필수 규칙

**모든 기안문(공문서)은 아래 규칙을 반드시 준수한다.** 참조 파일: `References/공문서_작성_양식_참조.md`, `References/doc_sample/2025 개정 공문서 작성법.hwpx`, `References/doc_sample/*.odt`

### 문서 구조 (두문 → 본문 → 결문)

```
[기관명]
수신  내부결재
(경유)
제목  [문서 제목]

1. 관련: [기관명]-[번호]([날짜], 「[문서명]」)
2. [목적 서술문]

  가. 운영기간: [날짜] ~ [날짜]
  나. 운영장소: [장소]
  다. 운영대상: [대상]
  라. 운영내용: [내용]
  마. 소요금액: 금[숫자]원(금[한글]원)
  바. 예산과목: [과목]

붙임  [첨부명] 1부.  끝.

기안자 직위 서명 / 검토자 직위 서명 / 결재권자 직위 서명
시행  [기관명-번호(날짜)]    접수  ( )
우 [우편번호] [주소] / [누리집] / 전화 [번호] / 전송 [번호] / [이메일] / 공개구분
```

### 핵심 표기 규칙

- **날짜**: `2025. 1. 6.` (아라비아 숫자, '일' 다음 마침표 필수) / 요일: `2025. 1. 6.(월)`
- **시간**: `09:00` (24시각제, 쌍점 양쪽 붙여씀)
- **금액**: `금221,750원(금이십이만일천칠백오십원)` — 숫자 먼저, 한글 괄호 안
- **끝.**: 붙임 표시문 끝에 2타 띄우고 `끝.`
- **항목기호**: `1., 2.` → `가., 나.` → `1), 2)` → `가), 나)` 순서 엄수
- **낫표**: 법률·규정명 = 「 」/ 책·신문명 = 『 』
- **외국어**: 한글 뒤 괄호 표기 `연구 개발(R&D)`

### 도서관 공문서 결재선

`주무관 → 사서팀장(또는 팀장) → 도서관장`

### 문서 종류별 본문 패턴

| 문서 종류 | 목적문 종결 | 금액 항목 |
|----------|------------|----------|
| 운영 계획 | "운영하고자 합니다" | 소요금액 |
| 운영 결과 | "보고합니다" | 지출금액 |
| 이용 실적 보고 | "보고합니다" | (표 형식) |

## Pending Issues

- Aladin TTB key entered in the sidebar is not being recognized by the agent (수서 에이전트 bug noted in `../library/수서 에이전트 수정사항.txt`)
- Real-time OPAC integration is not available; book DB is provided as an uploaded file; loan history is simulated via sample uploads
- OPAC search fallback: agent opens the library homepage search URL with the query pre-filled rather than querying directly
