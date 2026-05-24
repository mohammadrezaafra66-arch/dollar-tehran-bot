from collections import defaultdict
from datetime import datetime


class RuntimeFlowEvents:
    def __init__(self):
        self._events = defaultdict(list)

    def emit(self, trace_id: str, event_name: str, metadata=None):
        metadata = metadata or {}

        self._events[trace_id].append(
            {
                "event_name": event_name,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def snapshot(self):
        return dict(self._events)
