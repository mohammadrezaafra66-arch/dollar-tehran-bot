from datetime import datetime


class SchemaRegistry:
    def __init__(self):
        self._registry = {}

    def register(
        self,
        schema_name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._registry[schema_name] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

    def mark_degraded(self, schema_name: str):
        schema = self._registry.get(schema_name)

        if not schema:
            return

        schema["status"] = "degraded"

    def snapshot(self):
        return dict(self._registry)
