from collections import defaultdict
from datetime import datetime


class ProductionHardeningEvents:
    def __init__(self):
        self._events = defaultdict(list)

    def emit(
        self,
        component_name: str,
        name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._events[component_name].append(
            {
                "name": name,
                "metadata": metadata,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def snapshot(self):
        return dict(self._events)
