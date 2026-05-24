from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SessionOrchestrationConfig:
    session_timeout_seconds: int = int(
        os.getenv(
            "AFRA_SESSION_TIMEOUT_SECONDS",
            "1800",
        )
    )

    session_retry_limit: int = int(
        os.getenv(
            "AFRA_SESSION_RETRY_LIMIT",
            "3",
        )
    )

    max_parallel_sessions: int = int(
        os.getenv(
            "AFRA_MAX_PARALLEL_SESSIONS",
            "20",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_SESSION_ORCHESTRATION_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
