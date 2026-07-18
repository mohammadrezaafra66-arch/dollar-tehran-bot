import os
from dataclasses import dataclass

@dataclass
class Config:
    AFRAKALA_API_URL: str = os.getenv("AFRAKALA_API_URL", "http://192.168.170.8:8000")
    AFRAKALA_API_KEY: str = os.getenv("AFRAKALA_API_KEY", "")
    DEEPSEEK_BASE_URL: str = os.getenv("DEEPSEEK_BASE_URL", "http://localhost:11434")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-r1")
    DIVAR_DAILY_MESSAGE_LIMIT: int = int(os.getenv("DIVAR_DAILY_MESSAGE_LIMIT", "30"))
    DIVAR_MIN_DELAY: float = float(os.getenv("DIVAR_MIN_DELAY_SECONDS", "20"))
    DIVAR_MAX_DELAY: float = float(os.getenv("DIVAR_MAX_DELAY_SECONDS", "60"))
    DIVAR_PROFILE_DIR: str = os.getenv("DIVAR_PROFILE_DIR", "runtime/profiles/divar")
    DIVAR_MAX_ADS: int = int(os.getenv("DIVAR_MAX_ADS_PER_RUN", "200"))
    DB_PATH: str = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")
    OUTPUT_DIR: str = "output"
    HTTP_PROXY: str = os.getenv("HTTP_PROXY", "")
    ENABLE_MESSAGING: bool = os.getenv("ENABLE_MESSAGING", "false").lower() == "true"

cfg = Config()
