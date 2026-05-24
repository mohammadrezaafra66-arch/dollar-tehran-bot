from __future__ import annotations

import json
from typing import Any

from afra_market_data.db.storage import SQLiteStorage


VALID_JOB_STATUSES = {
    'pending',
    'running',
    'done',
    'failed',
    'skipped',
    'paused',
}


class JobRepository:
    def __init__(self, storage: SQLiteStorage | None = None):
        self.storage = storage or SQLiteStorage()
        self._initialize()

    def _initialize(self):
        self.storage.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                query TEXT NOT NULL,
                payload_json TEXT,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                last_error TEXT,
                result_json TEXT,
                started_at TEXT,
                finished_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self._ensure_column('jobs', 'result_json', 'TEXT')
        self._ensure_column('jobs', 'started_at', 'TEXT')
        self._ensure_column('jobs', 'finished_at', 'TEXT')
        self.storage.execute('CREATE INDEX IF NOT EXISTS idx_jobs_status_priority ON jobs(status, priority)')
        self.storage.execute('CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform)')

    def add_job(self, platform: str, query: str, payload: dict[str, Any] | None = None, priority: int = 1) -> int | None:
        payload_json = json.dumps(payload or {}, ensure_ascii=False)
        self.storage.execute('''
            INSERT INTO jobs (platform, query, payload_json, priority, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (platform, query, payload_json, priority))
        row = self.storage.fetch_one('SELECT last_insert_rowid() AS id')
        return row.get('id') if row else None

    def get_next_job(self) -> dict[str, Any] | None:
        row = self.storage.fetch_one('''
            SELECT * FROM jobs
            WHERE status = 'pending'
            ORDER BY priority DESC, id ASC
            LIMIT 1
        ''')
        return self._decode_job(row)

    def claim_next_job(self) -> dict[str, Any] | None:
        job = self.get_next_job()
        if not job:
            return None
        self.mark_running(job['id'])
        return self.get_job(job['id'])

    def get_job(self, job_id: int) -> dict[str, Any] | None:
        row = self.storage.fetch_one('SELECT * FROM jobs WHERE id = ?', (job_id,))
        return self._decode_job(row)

    def mark_running(self, job_id: int):
        self.storage.execute('''
            UPDATE jobs
            SET status = 'running',
                started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (job_id,))

    def mark_done(self, job_id: int, result: dict[str, Any] | None = None):
        result_json = json.dumps(result or {}, ensure_ascii=False)
        self.storage.execute('''
            UPDATE jobs
            SET status = 'done',
                result_json = ?,
                finished_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (result_json, job_id))

    def mark_failed(self, job_id: int, error: str):
        self.storage.execute('''
            UPDATE jobs
            SET status = 'failed',
                last_error = ?,
                retry_count = retry_count + 1,
                finished_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (error, job_id))

    def pause_job(self, job_id: int):
        self._set_status(job_id, 'paused')

    def resume_job(self, job_id: int):
        self._set_status(job_id, 'pending')

    def skip_job(self, job_id: int):
        self._set_status(job_id, 'skipped')

    def retry_job(self, job_id: int):
        self.storage.execute('''
            UPDATE jobs
            SET status = 'pending',
                last_error = NULL,
                result_json = NULL,
                started_at = NULL,
                finished_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (job_id,))

    def requeue_stale_running_jobs(self):
        self.storage.execute('''
            UPDATE jobs
            SET status = 'pending',
                updated_at = CURRENT_TIMESTAMP
            WHERE status = 'running'
        ''')

    def get_stats(self) -> dict[str, int]:
        rows = self.storage.fetch_all('''
            SELECT status, COUNT(*) AS count
            FROM jobs
            GROUP BY status
        ''')
        stats = {status: 0 for status in VALID_JOB_STATUSES}
        for row in rows:
            stats[row['status']] = row['count']
        return stats

    def list_jobs(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        if status:
            rows = self.storage.fetch_all('''
                SELECT * FROM jobs
                WHERE status = ?
                ORDER BY id DESC
                LIMIT ?
            ''', (status, limit))
        else:
            rows = self.storage.fetch_all('''
                SELECT * FROM jobs
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
        return [self._decode_job(row) for row in rows if row]

    def _set_status(self, job_id: int, status: str):
        if status not in VALID_JOB_STATUSES:
            raise ValueError(f'Invalid job status: {status}')
        self.storage.execute('''
            UPDATE jobs
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, job_id))

    def _decode_job(self, row: dict[str, Any] | None) -> dict[str, Any] | None:
        if not row:
            return None
        payload_json = row.get('payload_json') or '{}'
        result_json = row.get('result_json') or '{}'
        try:
            payload = json.loads(payload_json)
        except json.JSONDecodeError:
            payload = {}
        try:
            result = json.loads(result_json)
        except json.JSONDecodeError:
            result = {}
        decoded = dict(row)
        decoded['payload'] = payload
        decoded['result'] = result
        return decoded

    def _ensure_column(self, table_name: str, column_name: str, column_type: str):
        columns = self.storage.fetch_all(f'PRAGMA table_info({table_name})')
        existing = {column['name'] for column in columns}
        if column_name not in existing:
            self.storage.execute(f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}')
