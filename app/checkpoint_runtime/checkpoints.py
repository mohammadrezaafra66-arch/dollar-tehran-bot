from datetime import datetime, timedelta


class DistributedCheckpointRuntime:
    def __init__(self):
        self._checkpoints = {}

    def save(
        self,
        checkpoint_id: str,
        payload,
        ttl_seconds: int,
    ):
        self._checkpoints[checkpoint_id] = {
            "payload": payload,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (
                datetime.utcnow()
                + timedelta(seconds=ttl_seconds)
            ).isoformat(),
        }

    def load(self, checkpoint_id: str):
        checkpoint = self._checkpoints.get(checkpoint_id)

        if not checkpoint:
            return None

        expired = (
            datetime.utcnow().isoformat()
            > checkpoint["expires_at"]
        )

        if expired:
            self._checkpoints.pop(checkpoint_id, None)
            return None

        return checkpoint

    def snapshot(self):
        return dict(self._checkpoints)
