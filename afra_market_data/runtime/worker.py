from __future__ import annotations

import asyncio

from afra_market_data.core.logger import PlatformLogger
from afra_market_data.db.job_repository import JobRepository
from afra_market_data.drivers.registry import get_driver_class


class WorkerRuntime:
    def __init__(self, worker_name: str, job_repository: JobRepository):
        self.worker_name = worker_name
        self.job_repository = job_repository
        self.logger = PlatformLogger()
        self.running = False

    async def start(self):
        self.running = True
        self.logger.run_started(self.worker_name)

        while self.running:
            job = self.job_repository.claim_next_job()

            if not job:
                await asyncio.sleep(1)
                continue

            job_id = job['id']

            try:
                self.logger.activity(
                    'job_started',
                    worker=self.worker_name,
                    query=job['query'],
                    platform=job['platform'],
                    job_id=job_id,
                )

                result = await self.process_job(job)

                self.job_repository.mark_done(job_id, result)

                self.logger.activity(
                    'job_finished',
                    worker=self.worker_name,
                    query=job['query'],
                    platform=job['platform'],
                    job_id=job_id,
                )

            except Exception as exc:
                self.job_repository.mark_failed(job_id, str(exc))

                self.logger.error(
                    'job_failed',
                    worker=self.worker_name,
                    query=job['query'],
                    platform=job['platform'],
                    job_id=job_id,
                    error=str(exc),
                )

    async def process_job(self, job: dict):
        driver_class = get_driver_class(job['platform'])
        driver = driver_class()

        await driver.start()

        try:
            result = await driver.process(
                {
                    'query': job['query'],
                    **job.get('payload', {}),
                }
            )
        finally:
            await driver.stop()

        return result

    async def stop(self):
        self.running = False
        self.logger.run_finished(self.worker_name)
