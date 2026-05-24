from dataclasses import dataclass
import os


@dataclass(frozen=True)
class BrowserIsolationConfig:
    isolation_timeout_seconds: int = int(
        os.getenv(
            "AFRA_BROWSER_ISOLATION_TIMEOUT_SECONDS",
            "30",
        )
    )

    max_isolated_contexts: int = int(
        os.getenv(
            "AFRA_MAX_ISOLATED_CONTEXTS",
            "10",
        )
    )

    context_cleanup_interval_seconds: int = int(
        os.getenv(
            "AFRA_CONTEXT_CLEANUP_INTERVAL_SECONDS",
            "120",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_BROWSER_ISOLATION_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
