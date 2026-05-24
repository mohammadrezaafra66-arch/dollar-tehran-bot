"""OpenTelemetry bootstrap utilities for Afra Automation runtime.

This module centralizes tracing and metrics initialization so runtime code does
not depend directly on exporter details. Exporter endpoints are intentionally
config-driven for Kubernetes and multi-environment deployments.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TelemetrySettings:
    """Configuration for telemetry exporters."""

    service_name: str
    environment: str
    otlp_endpoint: Optional[str]
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "TelemetrySettings":
        """Build telemetry settings from environment variables."""

        return cls(
            service_name=os.getenv("AFRA_SERVICE_NAME", "divar-bot"),
            environment=os.getenv("AFRA_ENVIRONMENT", "development"),
            otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            enabled=os.getenv("AFRA_TELEMETRY_ENABLED", "true").lower() == "true",
        )


class OpenTelemetryBootstrap:
    """Initializes tracing and metrics with graceful fallback.

    The runtime remains usable even when OpenTelemetry packages are not installed.
    This is deliberate: observability must improve reliability, not become a new
    single point of failure.
    """

    def __init__(self, settings: Optional[TelemetrySettings] = None) -> None:
        self.settings = settings or TelemetrySettings.from_env()
        self.initialized = False

    def initialize(self) -> bool:
        """Initialize OpenTelemetry exporters if dependencies are installed."""

        if not self.settings.enabled:
            return False

        try:
            from opentelemetry import trace  # type: ignore
            from opentelemetry.sdk.resources import Resource  # type: ignore
            from opentelemetry.sdk.trace import TracerProvider  # type: ignore
            from opentelemetry.sdk.trace.export import BatchSpanProcessor  # type: ignore
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter  # type: ignore
        except Exception:
            self.initialized = False
            return False

        resource = Resource.create(
            {
                "service.name": self.settings.service_name,
                "deployment.environment": self.settings.environment,
            }
        )
        provider = TracerProvider(resource=resource)

        if self.settings.otlp_endpoint:
            exporter = OTLPSpanExporter(endpoint=self.settings.otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        self.initialized = True
        return True

    def tracer(self, name: str):
        """Return a tracer; falls back to OpenTelemetry no-op tracer."""

        from opentelemetry import trace  # type: ignore

        return trace.get_tracer(name)
