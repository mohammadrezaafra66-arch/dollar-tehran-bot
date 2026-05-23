import json

from divar_bot.core.worker_context import WorkerContext


class WorkerRuntime:
    def __init__(
        self,
        queue_backend,
        plugin_backend,
        result_backend,
        logger_backend,
        retry_policy=None,
    ):
        self.queue = queue_backend
        self.plugins = plugin_backend
        self.results = result_backend
        self.logger = logger_backend
        self.retry_policy = retry_policy

    def process_next(self, context: WorkerContext):
        if context.shutdown_requested:
            return None

        job = self.queue.get_next_job()

        if not job:
            return None

        try:
            payload = json.loads(job['payload'])
            plugin = self.plugins.get_plugin(job['plugin_name'])

            if not plugin:
                raise RuntimeError(f"Plugin not found: {job['plugin_name']}")

            plugin.start()
            extracted = plugin.extract(payload.get('url'))
            plugin.stop()

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

            raise
