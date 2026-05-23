class RetryPolicy:
    def __init__(self, max_retry=3):
        self.max_retry = max_retry

    def should_retry(self, retry_count):
        return retry_count < self.max_retry

    def next_status(self, retry_count):
        if self.should_retry(retry_count):
            return 'pending'
        return 'dead_letter'
