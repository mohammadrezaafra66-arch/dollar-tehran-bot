import asyncio
from datetime import datetime


class RealtimeDashboardRuntime:
    def __init__(self):
        self._clients = {}

    async def broadcast(
        self,
        client_id: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        try:
            result = await asyncio.wait_for(
                operation(),
                timeout=timeout_seconds,
            )

            self._clients[client_id] = {
                "status": "connected",
                "started_at": started_at,
                "updated_at": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as error:
            self._clients[client_id] = {
                "status": "failed",
                "started_at": started_at,
                "updated_at": datetime.utcnow().isoformat(),
                "error": str(error),
            }

            raise

    def snapshot(self):
        return dict(self._clients)
