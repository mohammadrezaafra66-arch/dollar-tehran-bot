from dataclasses import dataclass
import os


@dataclass(frozen=True)
class SchemaRuntimeConfig:
    validation_timeout_seconds: int = int(
        os.getenv(
            "AFRA_SCHEMA_VALIDATION_TIMEOUT_SECONDS",
            "10",
        )
    )

    max_validation_errors: int = int(
        os.getenv(
            "AFRA_SCHEMA_MAX_VALIDATION_ERRORS",
            "100",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_SCHEMA_RUNTIME_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )
