from datetime import datetime, timedelta


class TaskDeduplication:
    def __init__(self):
        self._tasks = {}

    def register(
        self,
        task_id: str,
        ttl_seconds: int,
    ):
        self._tasks[task_id] = {
            "expires_at": (
                datetime.utcnow()
                + timedelta(seconds=ttl_seconds)
            ).isoformat(),
            "created_at": datetime.utcnow().isoformat(),
        }

    def exists(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)

        if not task:
            return False

        return (
            datetime.utcnow().isoformat()
            < task["expires_at"]
        )

    def snapshot(self):
        return dict(self._tasks)
