from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RuntimeFlowConfig:
    execution_timeout_seconds: int = int(
        os.getenv(
            "AFRA_RUNTIME_FLOW_EXECUTION_TIMEOUT_SECONDS",
            "30",
        )
    )

    max_retry_attempts: int = int(
        os.getenv(
            "AFRA_RUNTIME_FLOW_MAX_RETRY_ATTEMPTS",
            "3",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_RUNTIME_FLOW_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )

    retry_backoff_seconds: int = int(
        os.getenv(
            "AFRA_RUNTIME_FLOW_RETRY_BACKOFF_SECONDS",
            "2",
        )
    )
