import asyncio

from app.runtime_flow.config import RuntimeFlowConfig
from app.runtime_flow.events import RuntimeFlowEvents
from app.runtime_flow.retry_policy import RuntimeFlowRetryPolicy


class RuntimeFlowOrchestrator:
    def __init__(self):
        self.config = RuntimeFlowConfig()
        self.events = RuntimeFlowEvents()
        self.retry_policy = RuntimeFlowRetryPolicy(
            max_retry_attempts=self.config.max_retry_attempts,
            retry_backoff_seconds=self.config.retry_backoff_seconds,
        )

    async def execute_node(
        self,
        node,
        payload,
        context,
    ):
        self.events.emit(
            context.trace_id,
            "node_execution_started",
        )

        async def operation():
            return await asyncio.wait_for(
                node.execute(payload, context),
                timeout=self.config.execution_timeout_seconds,
            )

        try:
            result = await self.retry_policy.execute(operation)

            self.events.emit(
                context.trace_id,
                "node_execution_succeeded",
            )

            return result

        except Exception as exc:
            self.events.emit(
                context.trace_id,
                "node_execution_failed",
                {
                    "error": str(exc),
                },
            )

            if self.config.degraded_mode_enabled:
                return {
                    "status": "degraded",
                    "trace_id": context.trace_id,
                }

            raise
