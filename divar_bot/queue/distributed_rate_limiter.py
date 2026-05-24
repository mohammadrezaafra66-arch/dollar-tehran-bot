import time


class DistributedRateLimiter:
    def __init__(self, redis_client, key='afra:rate-limit', limit=100, window_seconds=60):
        self.redis = redis_client
        self.key = key
        self.limit = limit
        self.window_seconds = window_seconds

    def allow(self, identity='global'):
        bucket_key = f'{self.key}:{identity}'
        current = self.redis.incr(bucket_key)

        if current == 1:
            self.redis.expire(bucket_key, self.window_seconds)

        return current <= self.limit

    def wait_until_allowed(self, identity='global', poll_interval=1):
        while not self.allow(identity):
            time.sleep(poll_interval)
