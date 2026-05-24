from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AIInferenceConfig:
    provider: str = os.getenv(
        "AFRA_AI_PROVIDER",
        "deepseek",
    )

    request_timeout_seconds: int = int(
        os.getenv(
            "AFRA_AI_TIMEOUT_SECONDS",
            "45",
        )
    )

    retry_limit: int = int(
        os.getenv(
            "AFRA_AI_RETRY_LIMIT",
            "4",
        )
    )

    circuit_breaker_threshold: int = int(
        os.getenv(
            "AFRA_AI_CIRCUIT_BREAKER_THRESHOLD",
            "6",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_AI_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
