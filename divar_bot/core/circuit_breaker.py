from datetime import datetime, timedelta


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_seconds=300):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failure_count = 0
        self.opened_at = None
        self.state = 'closed'

    def record_success(self):
        self.failure_count = 0
        self.opened_at = None
        self.state = 'closed'

    def record_failure(self):
        self.failure_count += 1

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            self.opened_at = datetime.utcnow()

    def can_execute(self):
        if self.state == 'closed':
            return True

        if not self.opened_at:
            return False

        recovery_at = self.opened_at + timedelta(seconds=self.recovery_seconds)

        if datetime.utcnow() >= recovery_at:
            self.state = 'half_open'
            return True

        return False
