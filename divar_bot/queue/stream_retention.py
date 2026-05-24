class StreamRetentionManager:
    def __init__(self, redis_client):
        self.redis = redis_client

    def trim(self, stream_name, max_length=100000):
        return self.redis.xtrim(
            stream_name,
            maxlen=max_length,
            approximate=True,
        )
