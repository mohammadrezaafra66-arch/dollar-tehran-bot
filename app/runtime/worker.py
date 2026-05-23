from __future__ import annotations

import asyncio
from typing import Optional

from app.core.logger import PlatformLogger
from app.core.queue_manager import QueueManager, QueueJob


class WorkerRuntime:
    def __init__(self, worker_name: str, queue_manager: QueueManager):
        self.worker_name = worker_name
        self.queue_manager = queue_manager
        self.logger = PlatformLogger()
        self.running = False

    async def start(self):
        self.running = True
        self.logger.run_started(self.worker_name)

        while self.running:
            job: Optional[QueueJob] = self.queue_manager.get_job()

            if not job:
                await asyncio.sleep(1)
                continue

            try:
                self.logger.activity(
                    'job_started',
                    worker=self.worker_name,
                    query=job.query,
                    platform=job.platform,
                )

                await self.process_job(job)

                self.logger.activity(
                    'job_finished',
                    worker=self.worker_name,
                    query=job.query,
                )

            except Exception as e:
                self.logger.error(
                    'job_failed',
                    worker=self.worker_name,
                    query=job.query,
                    error=str(e),
                )

    async def process_job(self, job: QueueJob):
        await asyncio.sleep(0.1)

    async def stop(self):
        self.running = False
        self.logger.run_finished(self.worker_name)
