from collections import defaultdict
from datetime import datetime


class SchemaRuntimeEvents:
    def __init__(self):
        self._events = defaultdict(list)

    def emit(
        self,
        schema_name: str,
        name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._events[schema_name].append(
            {
                "name": name,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def snapshot(self):
        return dict(self._events)
