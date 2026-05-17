from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


SCHEMA = '''
CREATE TABLE IF NOT EXISTS dollar_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_code TEXT NOT NULL,
    source_name TEXT NOT NULL,
    buy_price_toman INTEGER,
    sell_price_toman INTEGER,
    average_price_toman INTEGER,
    raw_price_text TEXT,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    error_message TEXT,
    raw_response_json TEXT,
    collected_at TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS run_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    source_code TEXT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    details_json TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS source_health (
    source_code TEXT PRIMARY KEY,
    source_name TEXT,
    status TEXT NOT NULL DEFAULT 'unknown',
    consecutive_failures INTEGER NOT NULL DEFAULT 0,
    total_success INTEGER NOT NULL DEFAULT 0,
    total_failed INTEGER NOT NULL DEFAULT 0,
    last_success_at TEXT,
    last_failed_at TEXT,
    last_error_type TEXT,
    last_error_message TEXT,
    last_http_status INTEGER,
    last_response_ms INTEGER,
    cooldown_until_epoch INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


class Storage:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = Path(sqlite_path)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def insert_price(self, row: dict[str, Any]) -> int:
        fields = [
            'source_code', 'source_name', 'buy_price_toman', 'sell_price_toman',
            'average_price_toman', 'raw_price_text', 'source_url', 'status',
            'error_message', 'raw_response_json', 'collected_at'
        ]
        values = []
        for field in fields:
            value = row.get(field)
            if field == 'raw_response_json' and value is not None:
                value = json.dumps(value, ensure_ascii=False)
            values.append(value)
        with self.connect() as conn:
            cur = conn.execute(
                'INSERT INTO dollar_prices (' + ','.join(fields) + ') VALUES (' + ','.join(['?'] * len(fields)) + ')',
                tuple(values),
            )
            conn.commit()
            return int(cur.lastrowid)

    def log(self, level: str, message: str, job_id: str | None = None, source_code: str | None = None, details: dict[str, Any] | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                'INSERT INTO run_logs (job_id, source_code, level, message, details_json) VALUES (?, ?, ?, ?, ?)',
                (job_id, source_code, level, message, json.dumps(details or {}, ensure_ascii=False)),
            )
            conn.commit()

    def latest_prices(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM dollar_prices ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
            return [dict(r) for r in rows]

    def latest_success_for_source(self, source_code: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                'SELECT * FROM dollar_prices WHERE source_code=? AND status=? ORDER BY id DESC LIMIT 1',
                (source_code, 'success'),
            ).fetchone()
            return dict(row) if row else None

    def latest_per_source(self) -> list[dict[str, Any]]:
        latest = {}
        for row in self.latest_prices(10000):
            latest.setdefault(row['source_code'], row)
        return sorted(latest.values(), key=lambda r: r.get('source_name') or '')

    def logs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM run_logs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
            return [dict(r) for r in rows]

    def record_health(self, source_code: str, source_name: str, ok: bool, collected_at: str, error_type: str | None = None, error_message: str | None = None, http_status: int | None = None, response_ms: int | None = None, cooldown_until_epoch: int = 0) -> None:
        current = self.get_source_health(source_code)
        failures = int(current.get('consecutive_failures', 0)) if current else 0
        total_success = int(current.get('total_success', 0)) if current else 0
        total_failed = int(current.get('total_failed', 0)) if current else 0
        if ok:
            failures = 0
            total_success += 1
            status = 'healthy'
            last_success_at = collected_at
            last_failed_at = current.get('last_failed_at') if current else None
        else:
            failures += 1
            total_failed += 1
            status = 'cooldown' if cooldown_until_epoch else 'error'
            last_success_at = current.get('last_success_at') if current else None
            last_failed_at = collected_at
        with self.connect() as conn:
            conn.execute(
                '''INSERT INTO source_health (
                    source_code, source_name, status, consecutive_failures, total_success, total_failed,
                    last_success_at, last_failed_at, last_error_type, last_error_message,
                    last_http_status, last_response_ms, cooldown_until_epoch, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(source_code) DO UPDATE SET
                    source_name=excluded.source_name,
                    status=excluded.status,
                    consecutive_failures=excluded.consecutive_failures,
                    total_success=excluded.total_success,
                    total_failed=excluded.total_failed,
                    last_success_at=excluded.last_success_at,
                    last_failed_at=excluded.last_failed_at,
                    last_error_type=excluded.last_error_type,
                    last_error_message=excluded.last_error_message,
                    last_http_status=excluded.last_http_status,
                    last_response_ms=excluded.last_response_ms,
                    cooldown_until_epoch=excluded.cooldown_until_epoch,
                    updated_at=CURRENT_TIMESTAMP''',
                (source_code, source_name, status, failures, total_success, total_failed, last_success_at, last_failed_at, error_type, error_message, http_status, response_ms, cooldown_until_epoch),
            )
            conn.commit()

    def get_source_health(self, source_code: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute('SELECT * FROM source_health WHERE source_code=?', (source_code,)).fetchone()
            return dict(row) if row else None

    def source_health(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM source_health ORDER BY source_name ASC').fetchall()
            return [dict(r) for r in rows]
