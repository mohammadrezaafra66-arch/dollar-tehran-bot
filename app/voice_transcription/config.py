from dataclasses import dataclass
import os


@dataclass(frozen=True)
class VoiceTranscriptionConfig:
    provider: str = os.getenv(
        "AFRA_TRANSCRIPTION_PROVIDER",
        "faster-whisper",
    )

    model_name: str = os.getenv(
        "AFRA_TRANSCRIPTION_MODEL_NAME",
        "large-v3",
    )

    request_timeout_seconds: int = int(
        os.getenv(
            "AFRA_TRANSCRIPTION_TIMEOUT_SECONDS",
            "120",
        )
    )

    retry_limit: int = int(
        os.getenv(
            "AFRA_TRANSCRIPTION_RETRY_LIMIT",
            "3",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_TRANSCRIPTION_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
