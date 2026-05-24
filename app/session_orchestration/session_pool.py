from datetime import datetime


class SessionPool:
    def __init__(self):
        self._pool = {}

    def register(
        self,
        session_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._pool[session_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

    def mark_degraded(self, session_id: str):
        session = self._pool.get(session_id)

        if not session:
            return

        session["status"] = "degraded"

    def snapshot(self):
        return dict(self._pool)
