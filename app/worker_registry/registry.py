from datetime import datetime


class PersistentWorkerRegistry:
    def __init__(self):
        self._workers = {}

    def register(
        self,
        worker_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._workers[worker_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "last_heartbeat": datetime.utcnow().isoformat(),
            "status": "active",
        }

    def heartbeat(self, worker_id: str):
        worker = self._workers.get(worker_id)

        if not worker:
            return

        worker["last_heartbeat"] = (
            datetime.utcnow().isoformat()
        )

    def mark_degraded(self, worker_id: str):
        worker = self._workers.get(worker_id)

        if not worker:
            return

        worker["status"] = "degraded"

    def snapshot(self):
        return dict(self._workers)
