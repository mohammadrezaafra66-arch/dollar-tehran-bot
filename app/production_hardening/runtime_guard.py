from datetime import datetime


class RuntimeGuard:
    def __init__(self):
        self._runtime_state = {}

    def register(
        self,
        component_name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._runtime_state[component_name] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "healthy",
        }

    def mark_degraded(self, component_name: str):
        component = self._runtime_state.get(
            component_name
        )

        if not component:
            return

        component["status"] = "degraded"

    def snapshot(self):
        return dict(self._runtime_state)
