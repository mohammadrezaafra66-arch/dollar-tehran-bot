from __future__ import annotations

from typing import Any

from afra_market_data.browser.anti_detection import AntiDetection
from afra_market_data.browser.browser_manager import BrowserManager, BrowserSettings
from afra_market_data.core.logger import PlatformLogger
from afra_market_data.drivers.base_driver import BaseDriver
from afra_market_data.services.torob_search import TorobSearchService


class TorobDriver(BaseDriver):
    def __init__(self):
        super().__init__('torob')
        self.logger = PlatformLogger()
        self.running = False
        self.search_service = TorobSearchService()

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

        search_result = await self.search_service.search(
            page=page,
            query=query,
        )

        self.logger.activity(
            'torob_search_completed',
            query=query,
            products_found=len(search_result.product_links),
        )

        return {
            'status': 'success',
            'query': query,
            'search_url': search_result.search_url,
            'page_title': search_result.page_title,
            'product_links': search_result.product_links,
            'product_count': len(search_result.product_links),
        }
