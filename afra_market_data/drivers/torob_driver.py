from __future__ import annotations

from typing import Any

from afra_market_data.browser.anti_detection import AntiDetection
from afra_market_data.browser.browser_manager import BrowserManager, BrowserSettings
from afra_market_data.core.logger import PlatformLogger
from afra_market_data.drivers.base_driver import BaseDriver


class TorobDriver(BaseDriver):
    def __init__(self):
        super().__init__('torob')
        self.logger = PlatformLogger()
        self.running = False
        self.browser = BrowserManager(
            BrowserSettings(
                headless=False,
                slow_mo=400,
                user_agent=AntiDetection.random_user_agent(),
            )
        )

    async def start(self):
        self.running = True
        await self.browser.start()
        self.logger.activity('torob_driver_started')

    async def stop(self):
        self.running = False
        await self.browser.close()
        self.logger.activity('torob_driver_stopped')

    async def process(self, payload: dict[str, Any]):
        query = payload.get('query')

        self.logger.activity(
            'torob_job_processing',
            query=query,
        )

        page = await self.browser.new_page()

        await page.goto('https://torob.com', wait_until='domcontentloaded')

        await AntiDetection.random_delay(1.5, 3.5)
        await AntiDetection.human_mouse_move(page)
        await AntiDetection.human_scroll(page)

        title = await page.title()

        self.logger.activity(
            'torob_home_loaded',
            title=title,
        )

        return {
            'status': 'success',
            'query': query,
            'page_title': title,
            'products': [],
            'sellers': [],
        }
