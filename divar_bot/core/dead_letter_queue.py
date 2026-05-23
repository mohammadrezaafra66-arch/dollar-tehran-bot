from datetime import datetime


class DeadLetterQueue:
    def __init__(self):
        self.items = []

    def add(self, job_id, reason, payload=None):
        self.items.append({
            'job_id': job_id,
            'reason': reason,
            'payload': payload or {},
            'failed_at': datetime.utcnow().isoformat(),
        })

    def all(self):
        return self.items
