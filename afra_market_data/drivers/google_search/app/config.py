# app/config.py - Google Search Driver
import os
import pandas as pd
from dataclasses import dataclass, field
from typing import Tuple, Optional


@dataclass
class Config:
    BASE_DIR: str = os.path.dirname(os.path.dirname(__file__))
    INPUT_DIR: str = os.path.join(BASE_DIR, 'input')
    OUTPUT_DIR: str = os.path.join(BASE_DIR, 'output')
    DATA_DIR: str = os.path.join(BASE_DIR, 'data')
    LOGS_DIR: str = os.path.join(BASE_DIR, 'logs')
    SCREENSHOTS_DIR: str = os.path.join(BASE_DIR, 'screenshots')

    MANAGEMENT_FILE: str = os.path.join(INPUT_DIR, 'google_search_management.xlsx')
    QUERIES_FILE: str = os.path.join(INPUT_DIR, 'google_search_input.xlsx')

    DATABASE_PATH: str = os.path.join(DATA_DIR, 'google_search.db')
    CHECKPOINT_FILE: str = os.path.join(DATA_DIR, 'checkpoints', 'checkpoint.json')

    LOG_FILE: str = os.path.join(LOGS_DIR, 'app.log')
    ERROR_LOG_FILE: str = os.path.join(LOGS_DIR, 'errors.log')

    MAX_RESULTS_PER_QUERY: int = 20
    MAX_PAGES_PER_QUERY: int = 2
    MAX_WEBSITES_TO_CRAWL: int = 20
    HEADLESS: bool = False
    SLOW_MO: int = 800
    WEBSITE_CRAWL_ENABLED: bool = True
    EXTRACT_EMAILS: bool = True
    EXTRACT_SOCIAL: bool = True

    DELAY_BETWEEN_RESULTS: Tuple[float, float] = (3.0, 7.0)
    DELAY_BETWEEN_QUERIES: Tuple[float, float] = (45.0, 90.0)
    DELAY_BETWEEN_PAGES: Tuple[float, float] = (5.0, 12.0)

    USE_CHROME_PROFILE: bool = os.getenv("USE_CHROME_PROFILE", "false").lower() == "true"
    USER_DATA_DIR: str = os.getenv("CHROME_USER_DATA_DIR", "")
    PROFILE_NAME: str = os.getenv("CHROME_PROFILE_NAME", "Default")

    MISTAKE_RATE: float = 0.02
    HUMAN_LIKE_TYPING: bool = True
    PAGE_TIMEOUT: int = 45000
    CAPTCHA_API_KEY: str = os.getenv("CAPTCHA_API_KEY", "")

    @classmethod
    def create_directories(cls):
        for dir_path in [cls.INPUT_DIR, cls.OUTPUT_DIR, cls.DATA_DIR, cls.LOGS_DIR, cls.SCREENSHOTS_DIR]:
            os.makedirs(dir_path, exist_ok=True)
        os.makedirs(os.path.join(cls.DATA_DIR, 'checkpoints'), exist_ok=True)

    @classmethod
    def load_from_excel(cls):
        if not os.path.exists(cls.MANAGEMENT_FILE):
            print(f"Using default settings (no management file)")
            return
        try:
            df = pd.read_excel(cls.MANAGEMENT_FILE, sheet_name='Config')
            settings = dict(zip(df['Setting'], df['Value']))
            if 'max_results_per_query' in settings:
                cls.MAX_RESULTS_PER_QUERY = int(settings['max_results_per_query'])
            if 'max_pages_per_query' in settings:
                cls.MAX_PAGES_PER_QUERY = int(settings['max_pages_per_query'])
            if 'headless' in settings:
                cls.HEADLESS = str(settings['headless']).upper() == 'TRUE'
            print("Settings loaded from management Excel")
        except Exception as e:
            print(f"Error loading management file: {e}")

    @classmethod
    def is_phase_enabled(cls, phase_name: str) -> bool:
        if not os.path.exists(cls.MANAGEMENT_FILE):
            return True
        try:
            df = pd.read_excel(cls.MANAGEMENT_FILE, sheet_name='Phases')
            row = df[df['Name'] == phase_name]
            if not row.empty:
                return bool(row.iloc[0]['Enabled'])
        except Exception:
            pass
        return True


Config.create_directories()
Config.load_from_excel()
