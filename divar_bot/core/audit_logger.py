from divar_bot.db.sqlite import SQLiteManager


class AuditLogger:
    def __init__(self, db=None):
        self.db = db or SQLiteManager()

    def log(self, action, entity_type, entity_id, details=''):
        with self.db.connection() as conn:
            conn.execute(
                '''
                INSERT INTO audit_logs (
                    action,
                    entity_type,
                    entity_id,
                    details
                ) VALUES (?, ?, ?, ?)
                ''',
                (
                    action,
                    entity_type,
                    entity_id,
                    details
                )
            )
