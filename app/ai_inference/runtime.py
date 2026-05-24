import asyncio
from datetime import datetime


class AIInferenceRuntime:
    def __init__(self):
        self._requests = {}

    async def execute(
        self,
        request_id: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        try:
            response = await asyncio.wait_for(
                operation(),
                timeout=timeout_seconds,
            )

            self._requests[request_id] = {
                "status": "completed",
                "started_at": started_at,
                "finished_at": datetime.utcnow().isoformat(),
            }

            return response

        except Exception as error:
            self._requests[request_id] = {
                "status": "failed",
                "started_at": started_at,
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(error),
            }

            raise

    def snapshot(self):
        return dict(self._requests)
