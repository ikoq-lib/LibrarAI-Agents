# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LibrarAI is a Korean public library AI management system consisting of three specialized Claude-powered agents:

- **평생학습 에이전트 (Lifelong Learning Agent)** — manages library program lifecycle: course planning, instructor hiring, student recruitment, attendance, and reporting across 7 workflow stages
- **수서 에이전트 (Acquisition Agent)** — manages book purchasing workflow using the Aladin Open API; handles 정기도서수서 (regular acquisitions) and 희망도서수서 (patron requests), including duplicate checking (ISBN, title, author)
- **이용자 응대 에이전트 (User Service Agent)** — kiosk-style patron-facing agent with voice + touch input; handles location guidance, loan/return/renewal, program info, and material recommendations

## Tech Stack

- **Frontend**: React (JSX), deployed on Vercel
- **Database**: Supabase (book DB, loan history, statistics)
- **AI**: Anthropic Claude API (claude-sonnet or latest)
- **External APIs**: Aladin Open API (TTB key) for book metadata
- **File processing**: xlsx.js (loaded dynamically from CDN) for KDC statistics Excel files

## Architecture Pattern

Each agent is a self-contained React component with:
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
- hwpx 변환은 `hwpx-autofil-conversion` 스킬을 사용한다.

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
