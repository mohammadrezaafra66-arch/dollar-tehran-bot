from dataclasses import dataclass
import os


@dataclass(frozen=True)
class TaskRuntimeConfig:
    deduplication_ttl_seconds: int = int(
        os.getenv(
            "AFRA_TASK_DEDUPLICATION_TTL_SECONDS",
            "3600",
        )
    )

    max_task_registry_size: int = int(
        os.getenv(
            "AFRA_MAX_TASK_REGISTRY_SIZE",
            "100000",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_TASK_RUNTIME_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
