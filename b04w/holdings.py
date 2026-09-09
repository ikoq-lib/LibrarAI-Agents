"""자관 장서 DB(Supabase public.books, 73,390행) 조회.

이 모듈이 있어서 프로그램이 '표대로'가 아니라 '우리 관 관행대로' 목록할 수 있다.
네 가지를 조회한다.

  1) 같은 ISBN의 기존 소장 → ctrl_no 재사용
  2) 같은 분류·같은 저자기호 → 충돌 시 ±1 조정
  3) 같은 총서의 기존 소장 → 저자기호·권차 계승
  4) 후보 강목의 세목 분포 → 자관이 실제로 쓰는 세목 확인 (Step 2-1 교차검증)

DB에 닿지 못하면 조용히 넘어가지 않는다 — 조회하지 못했다는 사실을 메모에 남긴다.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

from config import env


@dataclass
class Holding:
    reg_no: str = ""
    title: str = ""
    author: str = ""
    publisher: str = ""
    pub_year: int | None = None
    call_no: str = ""
    vol: str = ""
    loc_mark: str = ""
    ctrl_no: int | None = None
    isbn: str = ""


class Holdings:
    """PostgREST(Supabase) 읽기 전용 클라이언트."""

    def __init__(self, url: str = "", key: str = "", enabled: bool = True):
        self.enabled = enabled
        self.available = False
        self.reason = ""
        if not enabled:
            self.reason = "--no-db 로 비활성화됨"
            return
        try:
            self.url = (url or env("SUPABASE_URL")).rstrip("/")
            self.key = key or env("SUPABASE_ANON_KEY")
            self.available = True
        except EnvironmentError as exc:
            self.reason = str(exc)

    # ── 저수준 ──────────────────────────────────────────────────────────
    def _get(self, path: str, params: dict) -> list[dict]:
        if not self.available:
            return []
        query = urllib.parse.urlencode(params, safe="*.,()")
        request = urllib.request.Request(
            f"{self.url}/rest/v1/{path}?{query}",
            headers={"apikey": self.key, "Authorization": f"Bearer {self.key}"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))

    def _books(self, **params) -> list[Holding]:
        params.setdefault(
            "select", "reg_no,title,author,publisher,pub_year,call_no,vol,loc_mark,ctrl_no,isbn"
        )
        try:
            rows = self._get("books", params)
        except Exception as exc:
            self.reason = f"장서 DB 조회 실패: {exc}"
            self.available = False
            return []
        return [
            Holding(
                reg_no=row.get("reg_no") or "",
                title=row.get("title") or "",
                author=row.get("author") or "",
                publisher=row.get("publisher") or "",
                pub_year=row.get("pub_year"),
                call_no=row.get("call_no") or "",
                vol=row.get("vol") or "",
                loc_mark=row.get("loc_mark") or "",
                ctrl_no=row.get("ctrl_no"),
                isbn=row.get("isbn") or "",
            )
            for row in rows
        ]

    # ── 조회 ────────────────────────────────────────────────────────────
    def by_isbn(self, isbn: str) -> list[Holding]:
        if not isbn:
            return []
        return self._books(isbn=f"eq.{isbn}", limit=20)

    def by_call_prefix(self, kdc: str, author_mark: str) -> list[Holding]:
        """같은 분류·같은 저자기호의 기존 소장 (저자기호 충돌 확인용)."""
        if not (kdc and author_mark):
            return []
        return self._books(call_no=f"like.{kdc} {author_mark}*", limit=50)

    def by_title_author(self, title: str, author: str) -> list[Holding]:
        """총서 선례 탐색 — 목록의 총서란이 비어 있어도 DB로 확인한다."""
        if not title:
            return []
        head = title.split()[0][:6]
        rows = self._books(title=f"like.*{head}*", limit=50)
        if author:
            name = author.split()[0][:3]
            narrowed = [r for r in rows if name and name in (r.author or "")]
            if narrowed:
                return narrowed
        return rows

    def by_author(self, author: str) -> list[Holding]:
        """같은 저자의 자관 기존 소장 — 분류 선례로 쓴다.

        '이 저자의 앞 책을 우리 관이 어디에 두었는가'는 표보다 강한 근거다. 실제로
        임홍택의 기존 4건이 331.23·325.211에 있어 신간의 강목 판단이 갈렸다.
        """
        name = (author or "").strip()
        if len(name) < 2:
            return []
        return self._books(author=f"like.*{name}*", limit=20)

    def by_series(self, series_title: str) -> list[Holding]:
        if not series_title:
            return []
        head = series_title.split()[0][:8]
        return self._books(title=f"like.*{head}*", limit=50)

    def subdivision_stats(self, kdc: str, loc_mark: str | None = None) -> list[tuple[str, int]]:
        """후보 분류의 강목(정수 3자리) 아래에서 자관이 실제로 쓰는 세목 분포.

        예) 813.7 → '813'으로 시작하는 call_no 를 모아 세목별 건수를 센다.
        """
        base = (kdc or "").split(".")[0]
        if not base:
            return []
        params = {"select": "call_no,loc_mark", "call_no": f"like.{base}*", "limit": "5000"}
        if loc_mark is not None:
            params["loc_mark"] = f"eq.{loc_mark}" if loc_mark else "is.null"
        try:
            rows = self._get("books", params)
        except Exception as exc:
            self.reason = f"세목 분포 조회 실패: {exc}"
            return []
        counts: dict[str, int] = {}
        for row in rows:
            head = (row.get("call_no") or "").split(" ")[0]
            if head.startswith(base):
                counts[head] = counts.get(head, 0) + 1
        return sorted(counts.items(), key=lambda kv: -kv[1])[:12]

    def max_ctrl_no(self) -> int:
        try:
            rows = self._get("books", {"select": "ctrl_no", "order": "ctrl_no.desc", "limit": "1"})
        except Exception:
            return 0
        return int(rows[0]["ctrl_no"]) if rows and rows[0].get("ctrl_no") else 0
