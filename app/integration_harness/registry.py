from datetime import datetime


class IntegrationHarnessRegistry:
    def __init__(self):
        self._tests = {}

    def register(
        self,
        test_name: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._tests[test_name] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "registered",
        }

    def mark_failed(self, test_name: str):
        test = self._tests.get(test_name)

        if not test:
            return

        test["status"] = "failed"

    def snapshot(self):
        return dict(self._tests)
