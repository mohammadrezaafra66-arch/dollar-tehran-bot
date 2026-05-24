from dataclasses import dataclass
import os


@dataclass(frozen=True)
class OperationsCliConfig:
    command_timeout_seconds: int = int(
        os.getenv(
            "AFRA_OPERATIONS_COMMAND_TIMEOUT_SECONDS",
            "20",
        )
    )

    max_command_history: int = int(
        os.getenv(
            "AFRA_OPERATIONS_MAX_COMMAND_HISTORY",
            "1000",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_OPERATIONS_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
