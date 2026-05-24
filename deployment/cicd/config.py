from dataclasses import dataclass
import os


@dataclass(frozen=True)
class CICDPipelineConfig:
    pipeline_timeout_seconds: int = int(
        os.getenv(
            "AFRA_CICD_PIPELINE_TIMEOUT_SECONDS",
            "1800",
        )
    )

    max_parallel_jobs: int = int(
        os.getenv(
            "AFRA_CICD_MAX_PARALLEL_JOBS",
            "10",
        )
    )

    retry_limit: int = int(
        os.getenv(
            "AFRA_CICD_RETRY_LIMIT",
            "3",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_CICD_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
