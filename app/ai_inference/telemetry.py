from collections import defaultdict
from datetime import datetime


class AIInferenceTelemetry:
    def __init__(self):
        self._metrics = defaultdict(list)

    def track(
        self,
        metric_name: str,
        payload=None,
    ):
        payload = payload or {}

        self._metrics[metric_name].append(
            {
                "payload": payload,
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    def snapshot(self):
        return dict(self._metrics)
