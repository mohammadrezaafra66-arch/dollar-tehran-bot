"""Runtime tracing helpers for Afra Automation.

This module wraps OpenTelemetry in a dependency-tolerant API so the runtime can
create spans even when OpenTelemetry is not installed in local development. The
primary goal is end-to-end traceability across queue consumption, WAL writes,
rate limiting, browser execution, retries, and output persistence.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, Mapping, Optional


@dataclass(frozen=True)
class TraceAttributes:
    """Common trace attributes used across runtime spans."""

    trace_id: str = ""
    job_id: str = ""
    worker_id: str = ""
    instance_id: str = ""
    plugin_name: str = ""
    stage_name: str = ""
    extra: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        """Return normalized non-empty attributes."""

        data: Dict[str, Any] = {
            "afra.trace_id": self.trace_id,
            "afra.job_id": self.job_id,
            "afra.worker_id": self.worker_id,
            "afra.instance_id": self.instance_id,
            "afra.plugin_name": self.plugin_name,
            "afra.stage_name": self.stage_name,
        }
        data.update({f"afra.{key}": value for key, value in self.extra.items()})
        return {key: value for key, value in data.items() if value not in (None, "")}


class RuntimeTracer:
    """Small OpenTelemetry-safe tracer wrapper."""

    def __init__(self, name: str = "afra.runtime") -> None:
        self.name = name
        self._tracer = None
        self._available = False
        self._load()

    def _load(self) -> None:
        """Load OpenTelemetry tracer if available."""

        try:
            from opentelemetry import trace  # type: ignore

            self._tracer = trace.get_tracer(self.name)
            self._available = True
        except Exception:
            self._tracer = None
            self._available = False

    @contextmanager
    def span(
        self,
        name: str,
        attributes: Optional[TraceAttributes] = None,
        **extra_attributes: Any,
    ) -> Iterator[None]:
        """Create a span with graceful no-op fallback."""

        merged: Dict[str, Any] = {}
        if attributes:
            merged.update(attributes.as_dict())
        merged.update({f"afra.{key}": value for key, value in extra_attributes.items() if value not in (None, "")})

        if not self._available or self._tracer is None:
            yield
            return

        with self._tracer.start_as_current_span(name) as span:
            for key, value in merged.items():
                try:
                    span.set_attribute(key, value)
                except Exception:
                    continue
            try:
                yield
            except Exception as exc:
                try:
                    span.record_exception(exc)
                    span.set_attribute("afra.error", True)
                    span.set_attribute("afra.error_type", type(exc).__name__)
                finally:
                    raise


def event_trace_attributes(event: Any, stage_name: str = "") -> TraceAttributes:
    """Build trace attributes from a QueueEvent-like object."""

    return TraceAttributes(
        trace_id=getattr(event, "trace_id", ""),
        job_id=getattr(event, "event_id", ""),
        stage_name=stage_name,
        extra={"event_type": getattr(event, "event_type", "")},
    )
