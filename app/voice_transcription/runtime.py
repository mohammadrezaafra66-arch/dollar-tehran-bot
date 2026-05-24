import asyncio
from datetime import datetime


class VoiceTranscriptionRuntime:
    def __init__(self):
        self._jobs = {}

    async def transcribe(
        self,
        job_id: str,
        operation,
        timeout_seconds: int,
    ):
        started_at = datetime.utcnow().isoformat()

        try:
            result = await asyncio.wait_for(
                operation(),
                timeout=timeout_seconds,
            )

            self._jobs[job_id] = {
                "status": "completed",
                "started_at": started_at,
                "finished_at": datetime.utcnow().isoformat(),
            }

            return result

        except Exception as error:
            self._jobs[job_id] = {
                "status": "failed",
                "started_at": started_at,
                "finished_at": datetime.utcnow().isoformat(),
                "error": str(error),
            }

            raise

    def snapshot(self):
        return dict(self._jobs)
