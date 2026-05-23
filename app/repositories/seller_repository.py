from app.db.sqlite import SQLiteManager


class SellerRepository:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def create(self, seller_data):
        with self.db.connection() as conn:
            conn.execute(
                'INSERT INTO sellers (platform, display_name, source_id, confidence_score) VALUES (?, ?, ?, ?)',
                (
                    seller_data.get('platform', 'divar'),
                    seller_data.get('display_name'),
                    seller_data.get('source_id'),
                    seller_data.get('confidence_score', 0)
                )
            )

    def find_by_source_id(self, platform, source_id):
        with self.db.connection() as conn:
            cursor = conn.execute(
                'SELECT * FROM sellers WHERE platform = ? AND source_id = ? LIMIT 1',
                (platform, source_id)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
