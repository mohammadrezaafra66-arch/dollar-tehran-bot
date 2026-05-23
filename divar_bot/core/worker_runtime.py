import json

from divar_bot.core.memory_guard import MemoryGuard
from divar_bot.core.payload_validator import PayloadValidator
from divar_bot.core.worker_context import WorkerContext


class WorkerRuntime:
    def __init__(
        self,
        queue_backend,
        plugin_backend,
        result_backend,
        logger_backend,
        retry_policy=None,
        payload_validator=None,
        memory_guard=None,
    ):
        self.queue = queue_backend
        self.plugins = plugin_backend
        self.results = result_backend
        self.logger = logger_backend
        self.retry_policy = retry_policy
        self.payload_validator = payload_validator or PayloadValidator()
        self.memory_guard = memory_guard or MemoryGuard()

    def process_next(self, context: WorkerContext):
        if context.shutdown_requested:
            self.logger.warning(
                'worker_shutdown_requested',
                worker_id=context.worker_id,
            )
            return None

        if not self.memory_guard.is_memory_safe():
            snapshot = self.memory_guard.snapshot()

            self.logger.warning(
                'memory_pressure_detected',
                worker_id=context.worker_id,
                memory=snapshot,
            )

            return None

        job = self.queue.get_next_job()

        if not job:
            return None

        try:
            payload = json.loads(job['payload'])

            validation = self.payload_validator.validate(payload)

            if not validation['valid']:
                self.queue.fail_job(job['id'], validation['error'])

                self.logger.error(
                    'invalid_job_payload',
                    worker_id=context.worker_id,
                    job_id=job['id'],
                    validation=validation,
                )

                return None

            plugin = self.plugins.get_plugin(job['plugin_name'])

            if not plugin:
                raise RuntimeError(f"Plugin not found: {job['plugin_name']}")

            def extraction_operation():
                plugin.start()
                result = plugin.extract(payload.get('url'))
                plugin.stop()
                return result

            if self.retry_policy:
                extracted = self.retry_policy.execute(extraction_operation)
            else:
                extracted = extraction_operation()

            self.results.save(job['plugin_name'], extracted)
            self.queue.complete_job(job['id'])

            self.logger.info(
                'job_completed',
                worker_id=context.worker_id,
                job_id=job['id'],
            )

            return job

        except Exception as exc:
            self.queue.fail_job(job['id'], str(exc))

            self.logger.error(
                'job_failed',
                worker_id=context.worker_id,
                job_id=job['id'],
                error=str(exc),
            )

            return None
