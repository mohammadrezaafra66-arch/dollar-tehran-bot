"""Divar runtime worker integration.

This module connects Divar extraction logic to the distributed runtime:
- durable queue processing
- tracing
- structured logging
- rate limiting
- browser pool execution
- graceful draining

The goal is to make Divar extraction a runtime plugin instead of a standalone
script.
"""

from __future__ import annotations

from typing import Any, Dict

from divar_bot.infra.browser_pool import BrowserPool
from divar_bot.infra.draining import GracefulDrainingController
from divar_bot.infra.durable_job_runtime import DurableJobRuntime
from divar_bot.infra.kafka_adapter import QueueEvent
from divar_bot.infra.structured_logging import StructuredLogger
from divar_bot.infra.tracing import RuntimeTracer, event_trace_attributes


class DivarRuntimeWorker:
    """Runtime-aware Divar extraction worker."""

    def __init__(self) -> None:
        self.runtime = DurableJobRuntime()
        self.browser_pool = BrowserPool()
        self.draining = GracefulDrainingController()
        self.logger = StructuredLogger("afra.divar.worker")
        self.tracer = RuntimeTracer("afra.divar.worker")

    def process(self, event: QueueEvent) -> None:
        """Process one queue event through the durable runtime."""

        if self.draining.is_draining():
            self.logger.warning(
                "worker_draining_skip",
                trace_id=event.trace_id,
                event_id=event.event_id,
            )
            return

        decision = self.runtime.process_event(
            event=event,
            handler=self._extract,
            domain="divar.ir",
            identity="divar-runtime-worker",
        )

        self.logger.info(
            "job_runtime_decision",
            trace_id=event.trace_id,
            event_id=event.event_id,
            action=decision.action,
            reason=decision.reason,
            committed=decision.committed,
        )

    def _extract(self, event: QueueEvent) -> None:
        """Execute one Divar extraction job inside an isolated browser context."""

        with self.tracer.span(
            "divar.extract",
            attributes=event_trace_attributes(event, stage_name="extract"),
        ):
            bound_logger = self.logger.bind(
                trace_id=event.trace_id,
                event_id=event.event_id,
                stage="extract",
            )

            with self.browser_pool.session(metadata={"event_id": event.event_id}) as lease:
                page = lease.page
                url = str(event.payload.get("url", "https://divar.ir"))

                bound_logger.info(
                    "browser_navigation_start",
                    url=url,
                    browser_id=lease.browser_id,
                    lease_id=lease.lease_id,
                )

                try:
                    page.goto(url)
                    title = page.title()
                except Exception as exc:
                    bound_logger.exception(
                        "browser_navigation_failed",
                        url=url,
                        error_type=type(exc).__name__,
                    )
                    raise

                result: Dict[str, Any] = {
                    "url": url,
                    "title": title,
                }

                bound_logger.info(
                    "divar_extraction_completed",
                    extracted_title=title,
                    browser_id=lease.browser_id,
                )

                self._persist_result(result)

    def _persist_result(self, result: Dict[str, Any]) -> None:
        """Persist extraction result.

        Placeholder for database/export pipeline integration.
        """

        self.logger.info(
            "result_persisted",
            result_keys=list(result.keys()),
        )
