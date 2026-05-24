"""Structured JSON logging for Afra Automation runtime.

This module standardizes logs across workers, orchestrators, queue processors,
and browser runtimes. It is intentionally dependency-light and emits one JSON
object per line, suitable for Kubernetes logs, Loki, Elasticsearch, CloudWatch,
or any log forwarder.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Mapping, Optional


@dataclass(frozen=True)
class LogSettings:
    """Runtime logging settings."""

    service_name: str
    environment: str
    instance_id: str
    level: str

    @classmethod
    def from_env(cls) -> "LogSettings":
        """Build logging settings from environment variables."""

        return cls(
            service_name=os.getenv("AFRA_SERVICE_NAME", "divar-bot"),
            environment=os.getenv("AFRA_ENVIRONMENT", "development"),
            instance_id=os.getenv("DIVAR_BOT_INSTANCE_ID", socket.gethostname()),
            level=os.getenv("AFRA_LOG_LEVEL", "INFO"),
        )


class JsonLogFormatter(logging.Formatter):
    """Format records as single-line JSON."""

    def __init__(self, settings: LogSettings) -> None:
        super().__init__()
        self.settings = settings

    def format(self, record: logging.LogRecord) -> str:
        """Format one log record."""

        payload: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.settings.service_name,
            "environment": self.settings.environment,
            "instance_id": self.settings.instance_id,
        }

        extra = getattr(record, "extra_context", None)
        if isinstance(extra, Mapping):
            payload.update(dict(extra))

        if record.exc_info:
            payload["exception"] = "".join(traceback.format_exception(*record.exc_info))[:8000]

        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


class StructuredLogger:
    """Small adapter around stdlib logging with structured context support."""

    def __init__(self, name: str = "afra.runtime", settings: Optional[LogSettings] = None) -> None:
        self.settings = settings or LogSettings.from_env()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.settings.level.upper(), logging.INFO))
        self.logger.propagate = False

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonLogFormatter(self.settings))
            self.logger.addHandler(handler)

    def bind(self, **context: Any) -> "BoundStructuredLogger":
        """Return a logger with persistent context."""

        return BoundStructuredLogger(self.logger, context)

    def info(self, event: str, **context: Any) -> None:
        """Emit an info event."""

        self.logger.info(event, extra={"extra_context": {"event": event, **context}})

    def warning(self, event: str, **context: Any) -> None:
        """Emit a warning event."""

        self.logger.warning(event, extra={"extra_context": {"event": event, **context}})

    def error(self, event: str, **context: Any) -> None:
        """Emit an error event."""

        self.logger.error(event, extra={"extra_context": {"event": event, **context}})

    def exception(self, event: str, **context: Any) -> None:
        """Emit an exception event with traceback."""

        self.logger.exception(event, extra={"extra_context": {"event": event, **context}})


class BoundStructuredLogger:
    """Logger carrying persistent context like trace_id/job_id/worker_id."""

    def __init__(self, logger: logging.Logger, context: Mapping[str, Any]) -> None:
        self.logger = logger
        self.context = dict(context)

    def _payload(self, event: str, context: Mapping[str, Any]) -> Dict[str, Any]:
        return {"event": event, **self.context, **dict(context)}

    def info(self, event: str, **context: Any) -> None:
        self.logger.info(event, extra={"extra_context": self._payload(event, context)})

    def warning(self, event: str, **context: Any) -> None:
        self.logger.warning(event, extra={"extra_context": self._payload(event, context)})

    def error(self, event: str, **context: Any) -> None:
        self.logger.error(event, extra={"extra_context": self._payload(event, context)})

    def exception(self, event: str, **context: Any) -> None:
        self.logger.exception(event, extra={"extra_context": self._payload(event, context)})
