from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SenderOrchestrationConfig:
    sender_health_threshold: float = float(
        os.getenv(
            "AFRA_SENDER_HEALTH_THRESHOLD",
            "0.70",
        )
    )

    sender_cooldown_seconds: int = int(
        os.getenv(
            "AFRA_SENDER_COOLDOWN_SECONDS",
            "1800",
        )
    )

    max_parallel_senders: int = int(
        os.getenv(
            "AFRA_MAX_PARALLEL_SENDERS",
            "5",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_SENDER_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
