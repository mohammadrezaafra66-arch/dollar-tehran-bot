from app.db.sqlite import SQLiteManager


class JobRepository:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def all(self):
        with self.db.connection() as conn:
            cursor = conn.execute('SELECT * FROM jobs')
            return [dict(row) for row in cursor.fetchall()]
