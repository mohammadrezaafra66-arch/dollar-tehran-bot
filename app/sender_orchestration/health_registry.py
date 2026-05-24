from datetime import datetime


class SenderHealthRegistry:
    def __init__(self):
        self._senders = {}

    def register(self, sender_id: str, metadata=None):
        metadata = metadata or {}

        self._senders[sender_id] = {
            "metadata": metadata,
            "health_score": 1.0,
            "status": "active",
            "last_updated": datetime.utcnow().isoformat(),
        }

    def update_health(
        self,
        sender_id: str,
        health_score: float,
    ):
        sender = self._senders.get(sender_id)

        if not sender:
            return

        sender["health_score"] = max(
            0.0,
            min(health_score, 1.0),
        )

        sender["last_updated"] = (
            datetime.utcnow().isoformat()
        )

    def mark_degraded(self, sender_id: str):
        sender = self._senders.get(sender_id)

        if not sender:
            return

        sender["status"] = "degraded"

    def snapshot(self):
        return dict(self._senders)
