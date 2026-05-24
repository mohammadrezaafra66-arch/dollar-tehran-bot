import asyncio
from datetime import datetime


class OperationsCliRuntime:
    def __init__(self):
        self._history = []

    async def execute(
        self,
        command_name: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        result = await asyncio.wait_for(
            operation(),
            timeout=timeout_seconds,
        )

        self._history.append(
            {
                "command_name": command_name,
                "started_at": started_at,
                "finished_at": (
                    datetime.utcnow().isoformat()
                ),
            }
        )

        return result

    def history(self):
        return list(self._history)
