from datetime import datetime


class CICDJobRegistry:
    def __init__(self):
        self._jobs = {}

    def register(
        self,
        job_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._jobs[job_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "queued",
        }

    def mark_failed(self, job_id: str):
        job = self._jobs.get(job_id)

        if not job:
            return

        job["status"] = "failed"

    def snapshot(self):
        return dict(self._jobs)
