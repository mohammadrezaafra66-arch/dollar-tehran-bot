from datetime import datetime, timedelta


class ReplayableEventStore:
    def __init__(self):
        self._events = []

    def append(
        self,
        event_name: str,
        payload,
        ttl_seconds: int,
    ):
        self._events.append(
            {
                "event_name": event_name,
                "payload": payload,
                "created_at": (
                    datetime.utcnow().isoformat()
                ),
                "expires_at": (
                    datetime.utcnow()
                    + timedelta(seconds=ttl_seconds)
                ).isoformat(),
            }
        )

    def replay(self, batch_size: int):
        active_events = []

        for event in self._events:
            expired = (
                datetime.utcnow().isoformat()
                > event["expires_at"]
            )

            if expired:
                continue

            active_events.append(event)

        return active_events[:batch_size]

    def snapshot(self):
        return list(self._events)
