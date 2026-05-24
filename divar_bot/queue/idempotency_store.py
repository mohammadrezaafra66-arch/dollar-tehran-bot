from datetime import datetime


class IdempotencyStore:
    def __init__(self, redis_client, namespace='afra:idempotency'):
        self.redis = redis_client
        self.namespace = namespace

    def already_processed(self, operation_id):
        return self.redis.exists(f'{self.namespace}:{operation_id}')

    def mark_processed(self, operation_id, ttl_seconds=86400):
        key = f'{self.namespace}:{operation_id}'

        self.redis.set(
            key,
            datetime.utcnow().isoformat(),
            ex=ttl_seconds,
        )
