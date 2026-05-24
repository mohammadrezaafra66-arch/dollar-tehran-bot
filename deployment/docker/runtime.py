from datetime import datetime


class DockerRuntime:
    def __init__(self):
        self._containers = {}

    def register(
        self,
        container_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._containers[container_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "running",
        }

    def mark_unhealthy(self, container_id: str):
        container = self._containers.get(container_id)

        if not container:
            return

        container["status"] = "unhealthy"

    def snapshot(self):
        return dict(self._containers)
