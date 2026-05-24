from __future__ import annotations

import asyncio
from typing import Any

from afra_market_data.core.logger import PlatformLogger
from afra_market_data.drivers.base_driver import BaseDriver


class TorobDriver(BaseDriver):
    def __init__(self):
        super().__init__('torob')
        self.logger = PlatformLogger()
        self.running = False

    async def start(self):
        self.running = True
        self.logger.activity('torob_driver_started')

    async def stop(self):
        self.running = False
        self.logger.activity('torob_driver_stopped')

    async def process(self, payload: dict[str, Any]):
        query = payload.get('query')

        self.logger.activity(
            'torob_job_processing',
            query=query,
        )

        await asyncio.sleep(0.5)

        return {
            'status': 'success',
            'query': query,
            'products': [],
            'sellers': [],
        }
