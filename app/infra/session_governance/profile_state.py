from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ProfileSnapshot:
    profile_id: str
    value: float
    updated_at: str


class RuntimeProfileState:
    def __init__(self):
        self._states: dict[str, ProfileSnapshot] = {}

    def update(self, profile_id: str, value: float) -> ProfileSnapshot:
        bounded_value = max(0.0, min(value, 1.0))

        snapshot = ProfileSnapshot(
            profile_id=profile_id,
            value=bounded_value,
            updated_at=datetime.utcnow().isoformat(),
        )

        self._states[profile_id] = snapshot

        return snapshot

    def get(self, profile_id: str) -> ProfileSnapshot | None:
        return self._states.get(profile_id)
