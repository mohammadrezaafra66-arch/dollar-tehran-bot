from datetime import datetime


class EventStoreCleanup:
    def __init__(self, event_store):
        self.event_store = event_store

    def execute(self):
        retained_events = []

        for event in self.event_store.snapshot():
            expired = (
                datetime.utcnow().isoformat()
                > event["expires_at"]
            )

            if not expired:
                retained_events.append(event)

        self.event_store._events = retained_events
