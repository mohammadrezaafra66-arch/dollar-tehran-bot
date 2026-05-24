from datetime import datetime


class ConsumerRebalanceCoordinator:
    def __init__(self, redis_client, group_name='afra-workers'):
        self.redis = redis_client
        self.group_name = group_name

    def register_consumer(self, consumer_name, capacity=1):
        key = f'afra:consumers:{consumer_name}'

        self.redis.hset(key, mapping={
            'capacity': capacity,
            'registered_at': datetime.utcnow().isoformat(),
            'status': 'active',
        })

    def active_consumers(self):
        keys = self.redis.keys('afra:consumers:*')
        return [self.redis.hgetall(key) for key in keys]

    def rebalance_required(self, pending_threshold=100):
        pending = self.redis.xpending_range('afra:jobs', self.group_name, '-', '+', 100)
        return len(pending) >= pending_threshold
