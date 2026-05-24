from dataclasses import dataclass
import os


@dataclass(frozen=True)
class EventStoreConfig:
    event_ttl_seconds: int = int(
        os.getenv(
            "AFRA_EVENT_TTL_SECONDS",
            "604800",
        )
    )

    replay_batch_size: int = int(
        os.getenv(
            "AFRA_EVENT_REPLAY_BATCH_SIZE",
            "100",
        )
    )

    replay_retry_limit: int = int(
        os.getenv(
            "AFRA_EVENT_REPLAY_RETRY_LIMIT",
            "3",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_EVENT_STORE_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
