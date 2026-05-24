import asyncio
from datetime import datetime


class BrowserIsolationRuntime:
    def __init__(self):
        self._sessions = {}

    async def execute(
        self,
        isolation_id: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        result = await asyncio.wait_for(
            operation(),
            timeout=timeout_seconds,
        )

        self._sessions[isolation_id] = {
            "started_at": started_at,
            "finished_at": (
                datetime.utcnow().isoformat()
            ),
            "status": "isolated",
        }

        return result

    def snapshot(self):
        return dict(self._sessions)
