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

    TOROB_MIN_DELAY: float = float(os.getenv("TOROB_MIN_DELAY_SECONDS", "3"))
    TOROB_MAX_DELAY: float = float(os.getenv("TOROB_MAX_DELAY_SECONDS", "8"))
    TOROB_MAX_SELLERS: int = int(os.getenv("TOROB_MAX_SELLERS_PER_URL", "30"))
    TOROB_MAX_RETRY: int = int(os.getenv("TOROB_MAX_RETRY", "3"))
    SELLER_CRAWL_TIMEOUT: int = int(os.getenv("SELLER_CRAWL_TIMEOUT_SECONDS", "15"))
    MAX_SELLERS_TO_CRAWL: int = int(os.getenv("MAX_SELLERS_TO_CRAWL", "50"))
    TOROB_HEADLESS: bool = os.getenv("TOROB_HEADLESS", "true").lower() == "true"
    CRAWL_SELLER_SITES: bool = os.getenv("CRAWL_SELLER_SITES", "true").lower() == "true"

    DB_PATH: str = os.getenv("TOROB_DB_PATH", "data/torob.db")
    CHECKPOINT_FILE: str = "data/checkpoints/checkpoint.json"
    OUTPUT_DIR: str = "output"


cfg = Config()
