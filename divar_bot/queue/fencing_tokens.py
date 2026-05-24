class FencingTokenManager:
    def __init__(self, redis_client, key='afra:fencing-token'):
        self.redis = redis_client
        self.key = key

    def next_token(self):
        return int(self.redis.incr(self.key))
