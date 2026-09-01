---
name: feedback_naver_search_book_broken
description: 네이버 책 검색 API가 2026-09-01 서비스 종료됨 — 재시도하지 말고 WebSearch로 책소개·목차를 보강할 것
metadata:
  type: feedback
---

**네이버 책 검색 API는 종료됐다. 다시 호출하지 말 것.** 2026-09-01 확인:

```
mcp__naver-shopping__search-book → 404
{"errorMessage":"Invalid search api (존재하지 않는 검색 api 입니다.)","errorCode":"SE05"}
```

ISBN·서명·"해리포터" 등 확실히 존재하는 쿼리에서도 동일하게 실패한다. 같은 MCP 서버·같은 자격증명의 `search-blog`·`search-encyclopedia`는 정상 응답하므로 인증 만료나 서버 설정 문제가 아니라 네이버가 `/v1/search/book.json` 엔드포인트 자체를 내린 것이다. (네이버 쇼핑 검색 `/v1/search/shop.json`도 같은 시점에 종료됐다.)

**대응:** 재시도로 해결되지 않으므로 **1회 실패하면 바로 WebSearch로 전환**한다. 책소개·목차·저자 정보는 웹검색으로 충분히 확보되는 경우가 많다(2026-09-01 테스트에서 10권 중 8권 성공). 웹검색으로도 주제 판단 근거가 안 나오는 경우에만 `needs_info`로 표시하고, 표제·부가기호만으로 억지 분류하지 않는다.

**하지 말 것:** 서지 소스가 없다는 이유로 분류를 건너뛰거나, ISBN 부가기호의 내용분류를 KDC로 그대로 옮겨 적는 것. 부가기호는 출판사가 신고한 값이라 실제 내용과 어긋나는 사례가 흔하다(예: 요리사 산문집이 `03590` 생활과학으로 등록됨 — 실제 KDC는 814.7).

2026-09-01자로 프로젝트 전반에서 네이버 책 검색 경로가 삭제됐다(`api/naver-books.js` 삭제, B-01·B-02 스펙·PRD 재작성). 서지 외부 소스는 **SEOJI 단독**이다.

관련: [[kdc_juvenile_fiction_form_division]], [[project_series_kim_sanguk_physics]]
