from dataclasses import dataclass
import os


@dataclass(frozen=True)
class CheckpointRuntimeConfig:
    checkpoint_ttl_seconds: int = int(
        os.getenv(
            "AFRA_CHECKPOINT_TTL_SECONDS",
            "86400",
        )
    )

    checkpoint_retry_limit: int = int(
        os.getenv(
            "AFRA_CHECKPOINT_RETRY_LIMIT",
            "3",
        )
    )

    checkpoint_cleanup_interval_seconds: int = int(
        os.getenv(
            "AFRA_CHECKPOINT_CLEANUP_INTERVAL_SECONDS",
            "300",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_CHECKPOINT_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
