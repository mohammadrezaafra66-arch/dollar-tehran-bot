from datetime import datetime
import uuid


class EventBus:
    def __init__(self):
        self.handlers = {}

    def subscribe(self, event_type, handler):
        self.handlers.setdefault(event_type, []).append(handler)

    def publish(self, event_type, payload):
        event = {
            'event_id': str(uuid.uuid4()),
            'event_type': event_type,
            'payload': payload,
            'created_at': datetime.utcnow().isoformat(),
        }

        for handler in self.handlers.get(event_type, []):
            handler(event)

        return event
