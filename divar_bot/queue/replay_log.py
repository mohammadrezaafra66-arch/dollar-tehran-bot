import json
from datetime import datetime


class ReplayLog:
    def __init__(self, redis_client, stream='afra:replay-log'):
        self.redis = redis_client
        self.stream = stream

    def append(self, event_type, payload):
        self.redis.xadd(
            self.stream,
            {
                'event_type': event_type,
                'payload': json.dumps(payload),
                'recorded_at': datetime.utcnow().isoformat(),
            }
        )
