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
            rows = conn.execute('SELECT * FROM dollar_prices ORDER BY collected_at DESC, id DESC LIMIT ?', (limit,)).fetchall()
            return [dict(r) for r in rows]

    def latest_per_source(self) -> list[dict[str, Any]]:
        latest = {}
        for row in self.latest_prices(10000):
            latest.setdefault(row['source_code'], row)
        return sorted(latest.values(), key=lambda r: r.get('source_name') or '')

    def logs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute('SELECT * FROM run_logs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
            return [dict(r) for r in rows]
