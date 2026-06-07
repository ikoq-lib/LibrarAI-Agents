"""
프로젝트 루트의 .env 파일에서 환경변수를 로드합니다.
각 스크립트 상단에 다음 두 줄을 추가하세요:
    import load_env
    load_env.load()
"""
import os
from pathlib import Path


def load(dotenv_path: str | None = None) -> None:
    env_file = Path(dotenv_path) if dotenv_path else Path(__file__).parent / ".env"
    if not env_file.exists():
        raise FileNotFoundError(f".env 파일을 찾을 수 없습니다: {env_file}")

    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(f"환경변수 '{key}'가 설정되지 않았습니다. .env 파일을 확인하세요.")
    return value
