from app.db.sqlite import SQLiteManager


class AdRepository:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def create(self, ad_data):
        with self.db.connection() as conn:
            conn.execute(
                'INSERT INTO ads (platform, title, source_url) VALUES (?, ?, ?)',
                (
                    ad_data.get('platform', 'divar'),
                    ad_data.get('title'),
                    ad_data.get('source_url')
                )
            )
