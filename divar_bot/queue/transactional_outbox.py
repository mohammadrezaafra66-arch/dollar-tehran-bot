import json
from datetime import datetime


class TransactionalOutbox:
    def __init__(self, redis_client, stream='afra:outbox'):
        self.redis = redis_client
        self.stream = stream

    def publish(self, topic, payload):
        self.redis.xadd(
            self.stream,
            {
                'topic': topic,
                'payload': json.dumps(payload),
                'published_at': datetime.utcnow().isoformat(),
            }
        )
