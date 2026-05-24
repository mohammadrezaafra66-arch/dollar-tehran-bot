from __future__ import annotations

from typing import Any


SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "authorization",
}


REDACTED_VALUE = "***REDACTED***"


def redact_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    sanitized: dict[str, Any] = {}

    for key, value in data.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = REDACTED_VALUE
            continue

        if isinstance(value, dict):
            sanitized[key] = redact_sensitive_data(value)
            continue

        sanitized[key] = value

    return sanitized
