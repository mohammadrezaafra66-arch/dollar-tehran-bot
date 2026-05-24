"""Production health and metrics API for Afra Automation runtime.

This module exposes lightweight HTTP endpoints for Kubernetes probes,
Prometheus scraping, and operational dashboards. It is intentionally dependency
light and can run with the Python standard library only.

Endpoints:
- /healthz   : process is alive
- /readyz    : runtime dependencies are ready enough to receive work
- /metrics   : Prometheus text exposition format
- /snapshot  : JSON operational snapshot for dashboards and incident debugging

The API is not a business dashboard. It is an operational surface for SRE-style
runtime visibility.
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, Mapping, Optional


SnapshotProvider = Callable[[], Mapping[str, Any]]
ReadinessProvider = Callable[[], bool]


@dataclass(frozen=True)
class HealthApiSettings:
    """Configuration for the runtime health API."""

    host: str
    port: int
    service_name: str
    environment: str

    @classmethod
    def from_env(cls) -> "HealthApiSettings":
        """Build settings from environment variables."""

        return cls(
            host=os.getenv("AFRA_HEALTH_HOST", "0.0.0.0"),
            port=int(os.getenv("AFRA_HEALTH_PORT", "8080")),
            service_name=os.getenv("AFRA_SERVICE_NAME", "divar-bot"),
            environment=os.getenv("AFRA_ENVIRONMENT", "development"),
        )


@dataclass
class RuntimeHealthState:
    """Mutable health state shared by the HTTP handler."""

    started_at: float = field(default_factory=time.time)
    readiness_provider: Optional[ReadinessProvider] = None
    snapshot_provider: Optional[SnapshotProvider] = None
    metrics: Dict[str, float] = field(default_factory=dict)

    def is_ready(self) -> bool:
        """Return whether the runtime is ready."""

        if self.readiness_provider is None:
            return True
        try:
            return bool(self.readiness_provider())
        except Exception:
            return False

    def snapshot(self) -> Dict[str, Any]:
        """Return operational snapshot."""

        base = {
            "uptime_seconds": round(time.time() - self.started_at, 3),
            "ready": self.is_ready(),
            "metrics": self.metrics,
        }
        if self.snapshot_provider is None:
            return base
        try:
            extra = dict(self.snapshot_provider())
            return {**base, **extra}
        except Exception as exc:
            return {**base, "snapshot_error": f"{type(exc).__name__}: {str(exc)[:300]}"}

    def set_metric(self, name: str, value: float) -> None:
        """Set a numeric metric."""

        self.metrics[name] = float(value)

    def increment_metric(self, name: str, value: float = 1.0) -> None:
        """Increment a numeric metric."""

        self.metrics[name] = float(self.metrics.get(name, 0.0) + value)


class HealthApiServer:
    """Small HTTP server for health, readiness, metrics, and snapshots."""

    def __init__(
        self,
        settings: Optional[HealthApiSettings] = None,
        state: Optional[RuntimeHealthState] = None,
    ) -> None:
        self.settings = settings or HealthApiSettings.from_env()
        self.state = state or RuntimeHealthState()
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the HTTP server in a daemon thread."""

        if self._server is not None:
            return

        state = self.state
        settings = self.settings

        class Handler(BaseHTTPRequestHandler):
            """Runtime request handler."""

            def do_GET(self) -> None:  # noqa: N802 - stdlib API
                if self.path == "/healthz":
                    self._write_json(200, {"status": "ok", "service": settings.service_name})
                    return

                if self.path == "/readyz":
                    ready = state.is_ready()
                    self._write_json(200 if ready else 503, {"ready": ready, "service": settings.service_name})
                    return

                if self.path == "/snapshot":
                    self._write_json(200, {"service": settings.service_name, "environment": settings.environment, **state.snapshot()})
                    return

                if self.path == "/metrics":
                    self._write_text(200, self._prometheus_metrics())
                    return

                self._write_json(404, {"error": "not_found"})

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
                return

            def _write_json(self, status: int, payload: Mapping[str, Any]) -> None:
                body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _write_text(self, status: int, body_text: str) -> None:
                body = body_text.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _prometheus_metrics(self) -> str:
                snapshot = state.snapshot()
                lines = [
                    "# HELP afra_runtime_uptime_seconds Runtime uptime in seconds.",
                    "# TYPE afra_runtime_uptime_seconds gauge",
                    f"afra_runtime_uptime_seconds {snapshot.get('uptime_seconds', 0)}",
                    "# HELP afra_runtime_ready Runtime readiness state.",
                    "# TYPE afra_runtime_ready gauge",
                    f"afra_runtime_ready {1 if snapshot.get('ready') else 0}",
                ]
                for name, value in state.metrics.items():
                    safe_name = "afra_" + name.replace("-", "_").replace(".", "_")
                    lines.append(f"# TYPE {safe_name} gauge")
                    lines.append(f"{safe_name} {float(value)}")
                return "\n".join(lines) + "\n"

        self._server = ThreadingHTTPServer((self.settings.host, self.settings.port), Handler)
        self._thread = threading.Thread(target=self._server.serve_forever, name="afra-health-api", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the HTTP server."""

        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None
