class XAutoClaimRecovery:
    def __init__(
        self,
        redis_client,
        stream_name,
        group_name,
        consumer_name,
    ):
        self.redis = redis_client
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = consumer_name

    def recover_idle_messages(self, idle_ms=60000, count=100):
        response = self.redis.xautoclaim(
            self.stream_name,
            self.group_name,
            self.consumer_name,
            min_idle_time=idle_ms,
            start_id='0-0',
            count=count,
        )

        _, messages, _ = response

        return [
            {
                'id': job_id,
                'payload': payload,
            }
            for job_id, payload in messages
        ]
