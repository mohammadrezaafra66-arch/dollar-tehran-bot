from datetime import datetime


class TaskRuntimeCleanup:
    def __init__(self, deduplication_runtime):
        self.deduplication_runtime = (
            deduplication_runtime
        )

    def execute(self):
        snapshot = (
            self.deduplication_runtime.snapshot()
        )

        for task_id, task in snapshot.items():
            expired = (
                datetime.utcnow().isoformat()
                > task["expires_at"]
            )

            if expired:
                self.deduplication_runtime._tasks.pop(
                    task_id,
                    None,
                )
