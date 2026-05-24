from collections import defaultdict
from datetime import datetime


class CheckpointRuntimeEvents:
    def __init__(self):
        self._events = defaultdict(list)

    def emit(
        self,
        checkpoint_id: str,
        name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._events[checkpoint_id].append(
            {
                "name": name,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def snapshot(self):
        return dict(self._events)
