import asyncio
from datetime import datetime


class IntegrationHarnessRuntime:
    def __init__(self):
        self._results = []

    async def execute(
        self,
        test_name: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        result = await asyncio.wait_for(
            operation(),
            timeout=timeout_seconds,
        )

        self._results.append(
            {
                "test_name": test_name,
                "started_at": started_at,
                "finished_at": (
                    datetime.utcnow().isoformat()
                ),
                "status": "passed",
            }
        )

        return result

    def snapshot(self):
        return list(self._results)
