import asyncio
from datetime import datetime


class CICDPipelineRuntime:
    def __init__(self):
        self._pipelines = {}

    async def execute(
        self,
        pipeline_id: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        try:
            result = await asyncio.wait_for(
                operation(),
                timeout=timeout_seconds,
            )

            self._pipelines[pipeline_id] = {
                "status": "completed",
                "started_at": started_at,
                "finished_at": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as error:
            self._pipelines[pipeline_id] = {
                "status": "failed",
                "started_at": started_at,
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(error),
            }

            raise

    def snapshot(self):
        return dict(self._pipelines)
