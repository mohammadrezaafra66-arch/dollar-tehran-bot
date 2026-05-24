from datetime import datetime


class IsolatedContextPool:
    def __init__(self):
        self._contexts = {}

    def create(
        self,
        context_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._contexts[context_id] = {
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat(),
            "status": "isolated",
        }

    def release(self, context_id: str):
        context = self._contexts.get(context_id)

        if not context:
            return

        context["status"] = "released"

    def snapshot(self):
        return dict(self._contexts)
