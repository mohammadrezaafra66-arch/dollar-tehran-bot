from datetime import datetime


class HealthCheckService:
    def __init__(self, queue=None, db=None, metrics=None):
        self.queue = queue
        self.db = db
        self.metrics = metrics

    def check(self):
        checks = {
            'status': 'ok',
            'checked_at': datetime.utcnow().isoformat(),
            'database': self._check_database(),
            'queue': self._check_queue(),
            'metrics': self._check_metrics(),
        }

        if any(value == 'error' for key, value in checks.items() if key not in ['status', 'checked_at']):
            checks['status'] = 'degraded'

        return checks

    def _check_database(self):
        if not self.db:
            return 'not_configured'

        try:
            with self.db.connection() as conn:
                conn.execute('SELECT 1')
            return 'ok'
        except Exception:
            return 'error'

    def _check_queue(self):
        if not self.queue:
            return 'not_configured'
        return 'ok'

    def _check_metrics(self):
        if not self.metrics:
            return 'not_configured'
        return 'ok'
