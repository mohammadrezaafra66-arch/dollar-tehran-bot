class ConsumerDraining:
    def __init__(self, redis_client, group_name='afra-workers'):
        self.redis = redis_client
        self.group_name = group_name

    def drain(self, stream_name, consumer_name):
        pending = self.redis.xpending_range(
            stream_name,
            self.group_name,
            '-',
            '+',
            100,
            consumername=consumer_name,
        )

        return len(pending)
