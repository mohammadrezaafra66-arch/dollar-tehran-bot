from __future__ import annotations

import asyncio
from typing import Any

from app.infra.credentials.redaction import redact_sensitive_data


class CredentialResolutionError(Exception):
    pass


class RuntimeCredentialResolver:
    def __init__(
        self,
        provider,
        cache,
        logger,
        metrics,
        config,
    ):
        self.provider = provider
        self.cache = cache
        self.logger = logger
        self.metrics = metrics
        self.config = config

    async def resolve(
        self,
        identity_id: str,
    ) -> dict[str, Any]:
        cached = await self.cache.get(identity_id)

        if cached:
            self.metrics.increment(
                "credential.cache.hit"
            )

            return cached

        self.metrics.increment(
            "credential.cache.miss"
        )

        attempts = 0

        while attempts < self.config.max_retry:
            attempts += 1

            try:
                credential = await asyncio.wait_for(
                    self.provider.resolve(identity_id),
                    timeout=self.config.resolution_timeout_seconds,
                )

                await self.cache.set(
                    identity_id,
                    credential,
                    ttl=self.config.cache_ttl_seconds,
                )

                self.metrics.increment(
                    "credential.resolve.success"
                )

                return credential

            except Exception as exc:
                self.logger.warning(
                    "credential_resolution_retry",
                    extra={
                        "identity_id": identity_id,
                        "attempt": attempts,
                        "error": str(exc),
                    },
                )

                self.metrics.increment(
                    "credential.resolve.retry"
                )

                await asyncio.sleep(
                    min(2**attempts, 10)
                )

        if self.config.degraded_mode_enabled:
            fallback = await self.cache.get_stale(identity_id)

            if fallback:
                self.logger.warning(
                    "credential_degraded_resolution",
                    extra={
                        "identity_id": identity_id,
                        "fallback": redact_sensitive_data(fallback),
                    },
                )

                return fallback

        self.metrics.increment(
            "credential.resolve.failure"
        )

        raise CredentialResolutionError(
            f"failed_to_resolve:{identity_id}"
        )
