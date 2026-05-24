from datetime import datetime


class DashboardClientRegistry:
    def __init__(self):
        self._clients = {}

    def register(
        self,
        client_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._clients[client_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "connected",
        }

    def disconnect(self, client_id: str):
        client = self._clients.get(client_id)

        if not client:
            return

        client["status"] = "disconnected"

    def snapshot(self):
        return dict(self._clients)
