import json
import os
import time
from datetime import datetime

import redis


class RedisStreamsQueueBackend:
    def __init__(self, stream_name='afra:jobs', group_name='afra-workers'):
        self.stream_name = stream_name
        self.group_name = group_name
        self.consumer_name = os.getenv('DIVAR_BOT_INSTANCE_ID', 'local-worker')
        self.redis = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            decode_responses=True,
        )
        self._ensure_group()

    def _ensure_group(self):
        try:
            self.redis.xgroup_create(
                self.stream_name,
                self.group_name,
                id='0',
                mkstream=True,
            )
        except redis.exceptions.ResponseError as exc:
            if 'BUSYGROUP' not in str(exc):
                raise

    def publish_job(self, payload, job_type='extract', priority=5):
        return self.redis.xadd(
            self.stream_name,
            {
                'payload': json.dumps(payload),
                'job_type': job_type,
                'priority': priority,
                'created_at': datetime.utcnow().isoformat(),
            }
        )

    def claim_job(self, block_ms=5000):
        response = self.redis.xreadgroup(
            self.group_name,
            self.consumer_name,
            {self.stream_name: '>'},
            count=1,
            block=block_ms,
        )

        if not response:
            return None

        _, messages = response[0]
        job_id, data = messages[0]

        return {
            'id': job_id,
            'payload': data.get('payload'),
            'job_type': data.get('job_type'),
            'priority': data.get('priority'),
        }

    def acknowledge_job(self, job_id):
        self.redis.xack(self.stream_name, self.group_name, job_id)

    def move_to_dead_letter(self, job_id, payload, reason):
        self.redis.xadd(
            f'{self.stream_name}:dead-letter',
            {
                'job_id': job_id,
                'payload': json.dumps(payload),
                'reason': reason,
                'failed_at': datetime.utcnow().isoformat(),
            }
        )

    def pending_summary(self):
        return self.redis.xpending(self.stream_name, self.group_name)
