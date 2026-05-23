import os
import sqlite3
from contextlib import contextmanager


class SQLiteManager:
    def __init__(self, db_path=None, timeout_seconds=None):
        self.db_path = db_path or os.getenv('DIVAR_BOT_DATABASE_PATH', 'data/afra.db')
        self.timeout_seconds = timeout_seconds or int(os.getenv('DIVAR_BOT_DB_TIMEOUT_SECONDS', '30'))
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path, timeout=self.timeout_seconds)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout = 30000')
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self):
        with self.connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    plugin_name TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER DEFAULT 5,
                    status TEXT DEFAULT 'pending',
                    speed_profile TEXT DEFAULT 'safe',
                    retry_count INTEGER DEFAULT 0,
                    max_retry INTEGER DEFAULT 3,
                    scheduled_at TEXT,
                    locked_by_worker TEXT,
                    locked_until TEXT,
                    error_message TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    actor_type TEXT DEFAULT 'system',
                    actor_id TEXT DEFAULT 'platform',
                    details TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS extraction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plugin_name TEXT NOT NULL,
                    source_url TEXT,
                    raw_title TEXT,
                    raw_payload TEXT,
                    confidence_score REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sellers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    display_name TEXT,
                    source_id TEXT,
                    confidence_score REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    seller_id INTEGER,
                    title TEXT,
                    price TEXT,
                    source_url TEXT UNIQUE,
                    description TEXT,
                    city TEXT,
                    confidence_score REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_lock ON jobs(status, locked_until)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_extraction_plugin ON extraction_results(plugin_name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ads_platform ON ads(platform)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sellers_platform ON sellers(platform)')
