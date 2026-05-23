import time


class RetryPolicy:
    def __init__(self, max_attempts=3, base_delay_seconds=2, backoff_multiplier=2):
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.backoff_multiplier = backoff_multiplier

    def execute(self, operation):
        last_error = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()
            except Exception as exc:
                last_error = exc

                if attempt >= self.max_attempts:
                    break

                delay = self.base_delay_seconds * (self.backoff_multiplier ** (attempt - 1))
                time.sleep(delay)

        raise last_error
