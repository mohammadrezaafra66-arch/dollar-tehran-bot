import json
from datetime import datetime


class RetryScheduler:
    def __init__(self, redis_client, retry_stream='afra:retry'):
        self.redis = redis_client
        self.retry_stream = retry_stream

    def schedule_retry(self, job_id, payload, delay_seconds, reason):
        retry_at = datetime.utcnow().timestamp() + delay_seconds

        self.redis.zadd(
            self.retry_stream,
            {
                json.dumps({
                    'job_id': job_id,
                    'payload': payload,
                    'reason': reason,
                    'retry_at': retry_at,
                }): retry_at
            }
        )

    def due_retries(self):
        now = datetime.utcnow().timestamp()

        jobs = self.redis.zrangebyscore(
            self.retry_stream,
            min=0,
            max=now,
        )

        return [json.loads(job) for job in jobs]
