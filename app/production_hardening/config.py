from dataclasses import dataclass
import os


@dataclass(frozen=True)
class ProductionHardeningConfig:
    graceful_shutdown_timeout_seconds: int = int(
        os.getenv(
            "AFRA_GRACEFUL_SHUTDOWN_TIMEOUT_SECONDS",
            "60",
        )
    )

    memory_pressure_threshold_mb: int = int(
        os.getenv(
            "AFRA_MEMORY_PRESSURE_THRESHOLD_MB",
            "1024",
        )
    )

    healthcheck_interval_seconds: int = int(
        os.getenv(
            "AFRA_RUNTIME_HEALTHCHECK_INTERVAL_SECONDS",
            "30",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_PRODUCTION_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
