from datetime import datetime


class AIInferenceCircuitBreaker:
    def __init__(self, threshold: int):
        self.threshold = threshold
        self.failures = 0
        self.opened_at = None

    def record_success(self):
        self.failures = 0
        self.opened_at = None

    def record_failure(self):
        self.failures += 1

        if self.failures >= self.threshold:
            self.opened_at = datetime.utcnow().isoformat()

    def is_open(self) -> bool:
        return self.opened_at is not None
