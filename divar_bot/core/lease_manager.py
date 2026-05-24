from datetime import datetime, timedelta


class LeaseManager:
    def __init__(self, lease_seconds=300):
        self.lease_seconds = lease_seconds

    def create_lease_until(self, now=None):
        now = now or datetime.utcnow()
        return (now + timedelta(seconds=self.lease_seconds)).isoformat()

    def is_expired(self, lease_until, now=None):
        if not lease_until:
            return True

        now = now or datetime.utcnow()

        try:
            lease_time = datetime.fromisoformat(lease_until)
        except ValueError:
            return True

        return now >= lease_time

    def should_renew(self, lease_until, renewal_window_seconds=60, now=None):
        if not lease_until:
            return False

        now = now or datetime.utcnow()

        try:
            lease_time = datetime.fromisoformat(lease_until)
        except ValueError:
            return False

        return lease_time - now <= timedelta(seconds=renewal_window_seconds)
