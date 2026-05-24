from __future__ import annotations

from datetime import datetime, timedelta


class AdaptiveThrottling:
    def __init__(self):
        self._cooldowns: dict[str, str] = {}

    def apply(self, profile_id: str, cooldown_seconds: int):
        until = (
            datetime.utcnow() + timedelta(seconds=cooldown_seconds)
        ).isoformat()

        self._cooldowns[profile_id] = until

        return {
            "profile_id": profile_id,
            "cooldown_until": until,
        }

    def active(self, profile_id: str) -> bool:
        value = self._cooldowns.get(profile_id)

        if not value:
            return False

        return datetime.utcnow().isoformat() < value
