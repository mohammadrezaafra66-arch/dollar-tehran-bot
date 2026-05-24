from datetime import datetime


class KubernetesRuntime:
    def __init__(self):
        self._deployments = {}

    def register(
        self,
        deployment_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._deployments[deployment_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "running",
        }

    def mark_degraded(self, deployment_id: str):
        deployment = self._deployments.get(
            deployment_id
        )

        if not deployment:
            return

        deployment["status"] = "degraded"

    def snapshot(self):
        return dict(self._deployments)
