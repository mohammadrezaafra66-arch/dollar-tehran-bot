from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DockerRuntimeConfig:
    container_restart_policy: str = os.getenv(
        "AFRA_CONTAINER_RESTART_POLICY",
        "unless-stopped",
    )

    healthcheck_interval_seconds: int = int(
        os.getenv(
            "AFRA_CONTAINER_HEALTHCHECK_INTERVAL_SECONDS",
            "30",
        )
    )

    max_container_retries: int = int(
        os.getenv(
            "AFRA_MAX_CONTAINER_RETRIES",
            "5",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_DOCKER_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
