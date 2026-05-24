from datetime import datetime


class HotFailoverOrchestrator:
    def __init__(self, redis_client, namespace='afra:failover'):
        self.redis = redis_client
        self.namespace = namespace

    def activate_backup(self, primary_worker, backup_worker):
        payload = {
            'primary_worker': primary_worker,
            'backup_worker': backup_worker,
            'activated_at': datetime.utcnow().isoformat(),
            'status': 'active',
        }

        self.redis.hset(
            f'{self.namespace}:{primary_worker}',
            mapping=payload,
        )

        return payload
