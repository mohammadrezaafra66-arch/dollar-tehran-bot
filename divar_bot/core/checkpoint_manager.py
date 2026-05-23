from divar_bot.db.sqlite import SQLiteManager


class CheckpointManager:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def save(self, key, value):
        with self.db.connection() as conn:
            conn.execute(
                '''
                INSERT INTO checkpoints(key, value)
                VALUES (?, ?)
                ON CONFLICT(key)
                DO UPDATE SET value = excluded.value
                ''',
                (key, value)
            )

    def load(self, key):
        with self.db.connection() as conn:
            cursor = conn.execute(
                'SELECT value FROM checkpoints WHERE key = ?',
                (key,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            return row['value']
