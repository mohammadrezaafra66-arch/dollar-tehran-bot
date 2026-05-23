from app.db.sqlite import SQLiteManager


class AuditRepository:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def all(self):
        with self.db.connection() as conn:
            cursor = conn.execute('SELECT * FROM audit_logs ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
