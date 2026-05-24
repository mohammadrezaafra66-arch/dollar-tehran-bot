from dataclasses import dataclass
import os


@dataclass(frozen=True)
class RubikaAdapterConfig:
    api_base_url: str = os.getenv(
        "AFRA_RUBIKA_API_BASE_URL",
        "http://localhost:8080",
    )

    request_timeout_seconds: int = int(
        os.getenv(
            "AFRA_RUBIKA_REQUEST_TIMEOUT_SECONDS",
            "30",
        )
    )

    max_retry_attempts: int = int(
        os.getenv(
            "AFRA_RUBIKA_MAX_RETRY_ATTEMPTS",
            "3",
        )
    )

    sender_cooldown_seconds: int = int(
        os.getenv(
            "AFRA_RUBIKA_SENDER_COOLDOWN_SECONDS",
            "10",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_RUBIKA_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
