from __future__ import annotations

from typing import Any

from afra_market_data.browser.anti_detection import AntiDetection
from afra_market_data.browser.browser_manager import BrowserManager, BrowserSettings
from afra_market_data.core.logger import PlatformLogger
from afra_market_data.db.torob_repository import TorobRepository
from afra_market_data.drivers.base_driver import BaseDriver
from afra_market_data.services.torob_product_extractor import TorobProductExtractor
from afra_market_data.services.torob_search import TorobSearchService
from afra_market_data.services.torob_seller_extractor import TorobSellerExtractor


class TorobDriver(BaseDriver):
    def __init__(self):
        super().__init__('torob')
        self.logger = PlatformLogger()
        self.running = False

        self.search_service = TorobSearchService()
        self.product_extractor = TorobProductExtractor()
        self.seller_extractor = TorobSellerExtractor()
        self.repository = TorobRepository()

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

        product_snapshots = []
        seller_snapshots = []

        for product_link in search_result.product_links[:3]:
            try:
                snapshot = await self.product_extractor.extract(
                    page=page,
                    product_url=product_link,
                )

                product_data = snapshot.to_dict()
                product_snapshots.append(product_data)
                self.repository.save_product(query=query, product=product_data)

                sellers = await self.seller_extractor.extract(
                    page=page,
                    product_url=product_link,
                )

                for seller in sellers:
                    seller_data = seller.to_dict()
                    seller_snapshots.append(seller_data)
                    self.repository.save_seller(seller_data)

                self.logger.activity(
                    'torob_product_extracted',
                    title=snapshot.title,
                    url=product_link,
                    sellers_found=len(sellers),
                )

            except Exception as e:
                self.logger.error(
                    'torob_product_extraction_failed',
                    url=product_link,
                    error=str(e),
                )

        return {
            'status': 'success',
            'query': query,
            'search_url': search_result.search_url,
            'page_title': search_result.page_title,
            'product_links': search_result.product_links,
            'product_count': len(search_result.product_links),
            'products': product_snapshots,
            'sellers': seller_snapshots,
            'seller_count': len(seller_snapshots),
        }
