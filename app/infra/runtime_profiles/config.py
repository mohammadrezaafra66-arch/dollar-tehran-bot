from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RuntimeProfileConfig:
    anomaly_score_threshold: float = float(
        os.getenv(
            "AFRA_RUNTIME_PROFILE_ANOMALY_THRESHOLD",
            "0.7",
        )
    )

    cooldown_minutes: int = int(
        os.getenv(
            "AFRA_RUNTIME_PROFILE_COOLDOWN_MINUTES",
            "30",
        )
    )

    retry_limit: int = int(
        os.getenv(
            "AFRA_RUNTIME_PROFILE_RETRY_LIMIT",
            "3",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_RUNTIME_PROFILE_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
