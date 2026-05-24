from datetime import datetime


class LeaseAwareState:
    def __init__(self, redis_client, namespace='afra:leases'):
        self.redis = redis_client
        self.namespace = namespace

    def acquire(self, job_id, worker_id, lease_until, fencing_token):
        key = f'{self.namespace}:{job_id}'

        payload = {
            'worker_id': worker_id,
            'lease_until': lease_until,
            'fencing_token': fencing_token,
            'updated_at': datetime.utcnow().isoformat(),
        }

        self.redis.hset(key, mapping=payload)
        return payload

    def renew(self, job_id, lease_until):
        key = f'{self.namespace}:{job_id}'
        self.redis.hset(key, 'lease_until', lease_until)

    def release(self, job_id):
        self.redis.delete(f'{self.namespace}:{job_id}')

    def snapshot(self, job_id):
        return self.redis.hgetall(f'{self.namespace}:{job_id}')
