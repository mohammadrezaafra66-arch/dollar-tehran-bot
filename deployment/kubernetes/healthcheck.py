from datetime import datetime


class KubernetesHealthcheckRuntime:
    def __init__(self):
        self._healthchecks = {}

    def record(
        self,
        deployment_id: str,
        status: str,
    ):
        self._healthchecks[deployment_id] = {
            "status": status,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def snapshot(self):
        return dict(self._healthchecks)
