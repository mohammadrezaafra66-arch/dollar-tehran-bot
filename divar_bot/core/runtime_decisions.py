class RuntimeDecisions:
    def __init__(self, config=None):
        self.config = config or {}

    def should_retry(self, error_type):
        retryable = self.config.get('retryable_errors', [
            'TimeoutError',
            'ConnectionError',
            'TemporaryNetworkError',
        ])

        return error_type in retryable

    def should_throttle(self, queue_depth):
        threshold = self.config.get('throttle_queue_depth', 1000)
        return queue_depth >= threshold

    def get_stage_timeout(self, stage_name):
        stage_timeouts = self.config.get('stage_timeouts', {})
        return stage_timeouts.get(stage_name, 30)

    def get_max_records_per_batch(self):
        return self.config.get('max_records_per_batch', 100)
