import json
import uuid
from divar_bot.db.sqlite import SQLiteManager


class QueueManager:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def add_job(self, job_type, plugin_name, payload, priority=5, speed_profile='safe'):
        job_id = str(uuid.uuid4())

        with self.db.connection() as conn:
            conn.execute(
                '''
                INSERT INTO jobs (
                    id,
                    job_type,
                    plugin_name,
                    payload,
                    priority,
                    speed_profile,
                    status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    job_id,
                    job_type,
                    plugin_name,
                    json.dumps(payload),
                    priority,
                    speed_profile,
                    'pending'
                )
            )

        return job_id

    def get_next_job(self):
        with self.db.connection() as conn:
            cursor = conn.execute(
                '''
                SELECT *
                FROM jobs
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
                '''
            )

            row = cursor.fetchone()

            if not row:
                return None

            conn.execute(
                'UPDATE jobs SET status = ? WHERE id = ?',
                ('running', row['id'])
            )

            return dict(row)

    def complete_job(self, job_id):
        with self.db.connection() as conn:
            conn.execute(
                'UPDATE jobs SET status = ? WHERE id = ?',
                ('completed', job_id)
            )

    def fail_job(self, job_id, error_message):
        with self.db.connection() as conn:
            conn.execute(
                '''
                UPDATE jobs
                SET status = ?, error_message = ?, retry_count = retry_count + 1
                WHERE id = ?
                ''',
                ('failed', error_message, job_id)
            )
