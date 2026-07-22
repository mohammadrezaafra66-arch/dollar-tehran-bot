import os
from dataclasses import dataclass


@dataclass
class Config:
    AFRAKALA_API_URL: str = os.getenv("AFRAKALA_API_URL", "http://192.168.170.8:8000")
    AFRAKALA_API_KEY: str = os.getenv("AFRAKALA_API_KEY", "")

    TOROB_MIN_DELAY: float = float(os.getenv("TOROB_MIN_DELAY_SECONDS", "3"))
    TOROB_MAX_DELAY: float = float(os.getenv("TOROB_MAX_DELAY_SECONDS", "8"))
    TOROB_MAX_SELLERS: int = int(os.getenv("TOROB_MAX_SELLERS_PER_URL", "30"))
    TOROB_MAX_RETRY: int = int(os.getenv("TOROB_MAX_RETRY", "3"))
    SELLER_CRAWL_TIMEOUT: int = int(os.getenv("SELLER_CRAWL_TIMEOUT_SECONDS", "15"))
    MAX_SELLERS_TO_CRAWL: int = int(os.getenv("MAX_SELLERS_TO_CRAWL", "50"))
    TOROB_HEADLESS: bool = os.getenv("TOROB_HEADLESS", "true").lower() == "true"
    CRAWL_SELLER_SITES: bool = os.getenv("CRAWL_SELLER_SITES", "true").lower() == "true"

    DB_PATH: str = "data/torob.db"
    CHECKPOINT_FILE: str = "data/checkpoints/checkpoint.json"
    OUTPUT_DIR: str = "output"


cfg = Config()
