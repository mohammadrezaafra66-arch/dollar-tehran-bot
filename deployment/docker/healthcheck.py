from datetime import datetime


class DockerHealthcheckRuntime:
    def __init__(self):
        self._checks = {}

    def record(
        self,
        container_id: str,
        status: str,
    ):
        self._checks[container_id] = {
            "status": status,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def snapshot(self):
        return dict(self._checks)
