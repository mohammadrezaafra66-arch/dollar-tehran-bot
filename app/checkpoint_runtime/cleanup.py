from datetime import datetime


class CheckpointRuntimeCleanup:
    def __init__(self, checkpoint_runtime):
        self.checkpoint_runtime = checkpoint_runtime

    def execute(self):
        snapshot = (
            self.checkpoint_runtime.snapshot()
        )

        for checkpoint_id, checkpoint in (
            snapshot.items()
        ):
            expired = (
                datetime.utcnow().isoformat()
                > checkpoint["expires_at"]
            )

            if expired:
                self.checkpoint_runtime._checkpoints.pop(
                    checkpoint_id,
                    None,
                )
