from datetime import datetime


class PluginRegistry:
    def __init__(self):
        self._registry = {}

    def register(
        self,
        plugin_name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._registry[plugin_name] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

    def mark_degraded(self, plugin_name: str):
        plugin = self._registry.get(plugin_name)

        if not plugin:
            return

        plugin["status"] = "degraded"

    def snapshot(self):
        return dict(self._registry)
