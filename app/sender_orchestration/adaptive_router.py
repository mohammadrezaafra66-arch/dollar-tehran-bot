from datetime import datetime, timedelta


class AdaptiveSenderRouter:
    def __init__(self):
        self._cooldowns = {}

    def cooldown(
        self,
        sender_id: str,
        cooldown_seconds: int,
    ):
        self._cooldowns[sender_id] = (
            datetime.utcnow()
            + timedelta(seconds=cooldown_seconds)
        ).isoformat()

    def available(self, sender_id: str) -> bool:
        cooldown = self._cooldowns.get(sender_id)

        if not cooldown:
            return True

        return datetime.utcnow().isoformat() > cooldown
