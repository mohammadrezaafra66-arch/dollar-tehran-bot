from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


class SQLiteStorage:
    def __init__(self, db_path: str = 'database/leads.db'):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    query TEXT NOT NULL,
                    payload_json TEXT,
                    priority INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS run_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_name TEXT,
                    event TEXT NOT NULL,
                    details_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_name TEXT,
                    stage TEXT,
                    message TEXT NOT NULL,
                    details_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_name TEXT NOT NULL,
                    state_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform)')

    def execute(self, query: str, params: tuple[Any, ...] = ()):
        with self.connection() as conn:
            conn.execute(query, params)

    def fetch_all(self, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(query, params).fetchone()
            return dict(row) if row else None
