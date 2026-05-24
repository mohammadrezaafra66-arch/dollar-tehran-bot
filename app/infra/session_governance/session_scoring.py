from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SessionScoreSnapshot:
    profile_id: str
    score: float
    updated_at: str


class SessionScoring:
    def __init__(self):
        self._scores: dict[str, SessionScoreSnapshot] = {}

    def update(self, profile_id: str, score: float) -> SessionScoreSnapshot:
        bounded_score = max(0.0, min(score, 1.0))

        snapshot = SessionScoreSnapshot(
            profile_id=profile_id,
            score=bounded_score,
            updated_at=datetime.utcnow().isoformat(),
        )

        self._scores[profile_id] = snapshot

        return snapshot

    def get(self, profile_id: str) -> SessionScoreSnapshot | None:
        return self._scores.get(profile_id)

    def snapshot(self) -> dict[str, SessionScoreSnapshot]:
        return dict(self._scores)
