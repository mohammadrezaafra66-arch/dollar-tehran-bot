import json
from app.db.sqlite import SQLiteManager


class ExtractionRepository:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def save(self, plugin_name, data):
        with self.db.connection() as conn:
            conn.execute(
                '''
                INSERT INTO extraction_results (
                    plugin_name,
                    source_url,
                    raw_title,
                    raw_payload,
                    confidence_score
                ) VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    plugin_name,
                    data.get('source_url'),
                    data.get('title'),
                    json.dumps(data.get('raw_payload')),
                    data.get('confidence_score', 0)
                )
            )
