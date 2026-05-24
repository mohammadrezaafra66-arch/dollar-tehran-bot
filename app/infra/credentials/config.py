from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class CredentialRuntimeConfig:
    provider: str = os.getenv("AFRA_SECRET_PROVIDER", "vault")

    resolution_timeout_seconds: int = int(
        os.getenv(
            "AFRA_SECRET_RESOLUTION_TIMEOUT_SECONDS",
            "15",
        )
    )

    cache_ttl_seconds: int = int(
        os.getenv(
            "AFRA_SECRET_CACHE_TTL_SECONDS",
            "300",
        )
    )

    max_retry: int = int(
        os.getenv(
            "AFRA_SECRET_MAX_RETRY",
            "3",
        )
    )

    degraded_mode_enabled: bool = (
        os.getenv(
            "AFRA_SECRET_DEGRADED_MODE_ENABLED",
            "true",
        ).lower()
        == "true"
    )

    encryption_key: str = os.getenv(
        "AFRA_SECRET_CACHE_ENCRYPTION_KEY",
        "runtime-key-placeholder",
    )
