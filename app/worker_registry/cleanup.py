from datetime import datetime, timedelta


class WorkerRegistryCleanup:
    def __init__(
        self,
        registry,
        heartbeat_timeout_seconds: int,
    ):
        self.registry = registry
        self.heartbeat_timeout_seconds = (
            heartbeat_timeout_seconds
        )

    def execute(self):
        now = datetime.utcnow()

        for worker_id, worker in (
            self.registry.snapshot().items()
        ):
            heartbeat = datetime.fromisoformat(
                worker["last_heartbeat"]
            )

            expired = (
                now - heartbeat
                > timedelta(
                    seconds=self.heartbeat_timeout_seconds
                )
            )

            if expired:
                self.registry.mark_degraded(worker_id)
