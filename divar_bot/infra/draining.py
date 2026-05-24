"""Graceful draining controller for Afra Automation runtime.

Draining is required for safe Kubernetes rollouts, node drains, and operator
shutdowns. A draining worker must stop accepting new jobs, finish or safely route
in-flight jobs, release browser leases, and expose readiness=false before the pod
is terminated.
"""

from __future__ import annotations

import os
import signal
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


@dataclass(frozen=True)
class DrainSettings:
    """Configuration for graceful draining."""

    drain_file: Path
    termination_grace_seconds: int

    @classmethod
    def from_env(cls) -> "DrainSettings":
        """Build settings from environment variables."""

        return cls(
            drain_file=Path(os.getenv("AFRA_DRAIN_FILE", "/tmp/afra-draining")),
            termination_grace_seconds=int(os.getenv("AFRA_TERMINATION_GRACE_SECONDS", "60")),
        )


class GracefulDrainingController:
    """Coordinates runtime draining state and signal handling."""

    def __init__(self, settings: Optional[DrainSettings] = None) -> None:
        self.settings = settings or DrainSettings.from_env()
        self._draining = threading.Event()
        self._on_drain: Optional[Callable[[], None]] = None

    def install_signal_handlers(self, on_drain: Optional[Callable[[], None]] = None) -> None:
        """Install SIGTERM/SIGINT handlers for Kubernetes-safe shutdown."""

        self._on_drain = on_drain

        def _handler(signum, frame) -> None:  # type: ignore[no-untyped-def]
            self.start_draining(reason=f"signal:{signum}")
            if self._on_drain:
                self._on_drain()

        signal.signal(signal.SIGTERM, _handler)
        signal.signal(signal.SIGINT, _handler)

    def start_draining(self, reason: str = "manual") -> None:
        """Enter draining mode and write a local marker file."""

        self._draining.set()
        self.settings.drain_file.parent.mkdir(parents=True, exist_ok=True)
        self.settings.drain_file.write_text(
            f"started_at={datetime.utcnow().isoformat()}\nreason={reason}\n",
            encoding="utf-8",
        )

    def stop_draining(self) -> None:
        """Leave draining mode and remove marker file."""

        self._draining.clear()
        if self.settings.drain_file.exists():
            self.settings.drain_file.unlink()

    def is_draining(self) -> bool:
        """Return whether the runtime should stop accepting new jobs."""

        return self._draining.is_set() or self.settings.drain_file.exists()

    def readiness(self) -> bool:
        """Readiness provider compatible with HealthApiServer."""

        return not self.is_draining()
