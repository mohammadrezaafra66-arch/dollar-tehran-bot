import json
from datetime import datetime


class PoisonMessageQuarantine:
    def __init__(self, redis_client, stream='afra:poison'):
        self.redis = redis_client
        self.stream = stream

    def quarantine(self, job_id, payload, reason, retries):
        self.redis.xadd(
            self.stream,
            {
                'job_id': job_id,
                'payload': json.dumps(payload),
                'reason': reason,
                'retries': retries,
                'quarantined_at': datetime.utcnow().isoformat(),
            }
        )
