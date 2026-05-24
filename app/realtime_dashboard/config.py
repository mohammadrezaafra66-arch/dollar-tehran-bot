from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RealtimeDashboardConfig:
    websocket_timeout_seconds: int = int(
        os.getenv(
            "AFRA_DASHBOARD_WEBSOCKET_TIMEOUT_SECONDS",
            "30",
        )
    )

    refresh_interval_seconds: int = int(
        os.getenv(
            "AFRA_DASHBOARD_REFRESH_INTERVAL_SECONDS",
            "5",
        )
    )

    max_dashboard_clients: int = int(
        os.getenv(
            "AFRA_MAX_DASHBOARD_CLIENTS",
            "100",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_DASHBOARD_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
