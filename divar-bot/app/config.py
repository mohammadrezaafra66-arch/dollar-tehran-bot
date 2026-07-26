import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file()


@dataclass
class Config:
    AFRAKALA_API_URL: str = os.getenv("AFRA_API_URL") or os.getenv("AFRAKALA_API_URL", "http://192.168.170.8:8000")
    AFRAKALA_API_KEY: str = os.getenv("AFRA_API_KEY") or os.getenv("AFRAKALA_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "http://localhost:11434")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-r1")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DIVAR_DAILY_MESSAGE_LIMIT: int = int(os.getenv("DIVAR_DAILY_MESSAGE_LIMIT", "30"))
    DIVAR_MIN_DELAY: float = float(os.getenv("DIVAR_MIN_DELAY_SECONDS", "20"))
    DIVAR_MAX_DELAY: float = float(os.getenv("DIVAR_MAX_DELAY_SECONDS", "60"))
    DIVAR_PROFILE_DIR: str = os.getenv("DIVAR_PROFILE_DIR", "runtime/profiles/divar")
    DIVAR_PROFILE_COUNT: int = int(os.getenv("DIVAR_PROFILE_COUNT", "5"))
    DIVAR_MAX_ADS: int = int(os.getenv("DIVAR_MAX_ADS_PER_RUN", "200"))
    DB_PATH: str = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")
    OUTPUT_DIR: str = "output"
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
    ENABLE_MESSAGING: bool = os.getenv("ENABLE_MESSAGING", "false").lower() == "true"


cfg = Config()
