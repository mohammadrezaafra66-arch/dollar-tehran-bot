from __future__ import annotations

import asyncio
from datetime import datetime

from afra_market_data.core.logger import PlatformLogger


class SchedulerEngine:
    def __init__(self, interval_seconds: int = 60):
        self.interval_seconds = interval_seconds
        self.running = False
        self.logger = PlatformLogger()

    async def start(self):
        self.running = True
        self.logger.activity('scheduler_started', interval=self.interval_seconds)

        while self.running:
            await self.run_cycle()
            await asyncio.sleep(self.interval_seconds)

    async def run_cycle(self):
        self.logger.activity(
            'scheduler_cycle',
            timestamp=datetime.now().isoformat(),
        )

    async def stop(self):
        self.running = False
        self.logger.activity('scheduler_stopped')
