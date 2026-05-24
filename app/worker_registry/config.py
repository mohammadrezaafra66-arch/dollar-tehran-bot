from dataclasses import dataclass
import os


@dataclass(frozen=True)
class WorkerRegistryConfig:
    heartbeat_timeout_seconds: int = int(
        os.getenv(
            "AFRA_WORKER_HEARTBEAT_TIMEOUT_SECONDS",
            "60",
        )
    )

    registry_cleanup_interval_seconds: int = int(
        os.getenv(
            "AFRA_WORKER_REGISTRY_CLEANUP_INTERVAL_SECONDS",
            "120",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_WORKER_REGISTRY_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
