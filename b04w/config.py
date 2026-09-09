"""B-04-W 자료조직 프로그램 — 자관 고정값과 환경설정.

여기 있는 값은 전부 우리 관 목록 정책에서 온 확정값이다. 근거는
`.claude/agents/b-04-w-cataloging-worker.md`와 국립중앙도서관 실물 MARC 52건이다.
값을 바꾸려면 그 근거부터 바꿔야 한다.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

# ── 경로 ────────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parent
DATA_DIR = HERE / "data"
KDC6_TEXT = PROJECT_ROOT / "References" / "KDC6_for_learning.txt"

# ── 자관 목록 정책 고정값 ───────────────────────────────────────────────
ORG_CODE = "148024"           # 040 목록작성기관 부호
LDR_VALUE = "00000nam a2200000 c 4500"   # 24자리. 00-04·12-16은 적재 시스템이 덮어쓴다
CTRL_NO_WIDTH = 12            # 001 = ctrl_no를 왼쪽 0으로 채운 12자리

# 대상 자료실 → (049 $f 별치기호, 008/22 대상독자부호)
AUDIENCE = {
    "성인": ("", " "),
    "어린이": ("J", "b"),
    "유아": ("유", "a"),
}

# 생성 금지 필드 — QA가 이 태그의 존재 자체를 실패로 본다
FORBIDDEN_TAGS = ("100", "110", "111", "052", "023", "082", "880")

# 출력 tag-order
TAG_ORDER = [
    "020", "040", "041", "049", "056", "090", "240", "245", "246", "250",
    "260", "300", "490", "500", "504", "505", "520", "521", "536", "546",
    "650", "651", "653", "700", "710", "740", "830", "900", "950",
]

# 필수 필드 (QA)
REQUIRED_TAGS = ["020", "040", "049", "056", "090", "245", "260", "300", "950"]

# ── LLM ─────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "qwen/qwen3.7-plus"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── 외부 API ────────────────────────────────────────────────────────────
SEOJI_URL = "https://www.nl.go.kr/seoji/SearchApi.do"


def load_env() -> None:
    """프로젝트 루트의 .env / .env.local 을 os.environ 에 올린다(기존 값 우선)."""
    for name in (".env", ".env.local"):
        path = PROJECT_ROOT / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def env(key: str, required: bool = True) -> str:
    value = os.environ.get(key, "")
    if not value and required:
        raise EnvironmentError(
            f"환경변수 '{key}'가 없습니다. {PROJECT_ROOT}/.env 또는 .env.local 을 확인하세요."
        )
    return value


def with_deadline(func, seconds: float, *args, **kwargs):
    """`func`에 **총** 제한시간을 건다.

    urllib 의 `timeout=` 은 소켓 한 번의 읽기에만 걸려서, 응답이 조금씩 흘러오면
    영원히 매달릴 수 있다(실측: OpenRouter 분류 호출 1건이 timeout=180 인데도 7분
    넘게 반환하지 않았다). 배치에서는 워커 한 자리가 그대로 묶이므로 총시간 기준으로
    끊는다. 매달린 스레드는 daemon 이라 프로세스 종료를 막지 않는다.
    """
    box: dict = {}

    def run() -> None:
        try:
            box["value"] = func(*args, **kwargs)
        except BaseException as exc:      # noqa: BLE001 — 호출측에 그대로 넘긴다
            box["error"] = exc

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    worker.join(seconds)
    if worker.is_alive():
        raise TimeoutError(f"{seconds:.0f}초 안에 응답이 오지 않았습니다.")
    if "error" in box:
        raise box["error"]
    return box["value"]
