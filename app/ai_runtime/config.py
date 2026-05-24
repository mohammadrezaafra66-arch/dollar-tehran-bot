from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AIRuntimeConfig:
    provider: str = os.getenv(
        "AFRA_AI_PROVIDER",
        "ollama",
    )

    model_name: str = os.getenv(
        "AFRA_AI_MODEL_NAME",
        "llama3.1:8b",
    )

    api_base_url: str = os.getenv(
        "AFRA_AI_API_BASE_URL",
        "http://localhost:11434",
    )

    request_timeout_seconds: int = int(
        os.getenv(
            "AFRA_AI_REQUEST_TIMEOUT_SECONDS",
            "60",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_AI_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
