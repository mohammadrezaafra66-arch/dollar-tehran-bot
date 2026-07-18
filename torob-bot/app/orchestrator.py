import asyncio
import json
import os
from typing import Any

from app.api_sync import ApiSync
from app.config import cfg
from app.database import TorobDatabase
from app.deduplicator import Deduplicator
from app.excel_exporter import ExcelExporter
from app.torob_scraper import TorobScraper
from app.website_crawler import WebsiteCrawler


class Orchestrator:
    def __init__(self) -> None:
        self.scraper = TorobScraper()
        self.crawler = WebsiteCrawler()
        self.db = TorobDatabase()
        self.exporter = ExcelExporter()
        self.sync = ApiSync()

    async def run(self, query: str) -> dict[str, Any]:
        product_results = await self.scraper.search_products(query)
        all_sellers: list[dict[str, Any]] = []
        crawler_stats = {"valid_external_urls": 0, "skipped": 0}

        for product in product_results[:3]:
            try:
                seller_source = product.get("prk") or product.get("url")
                sellers = await self.scraper.extract_sellers(seller_source)
                for seller in sellers[: cfg.TOROB_MAX_SELLERS]:
                    lead = {
                        "store_name": seller.get("name", "unknown"),
                        "phone": None,
                        "email": None,
                        "store_url": seller.get("seller_url"),
                        "torob_url": seller.get("torob_url"),
                        "price_on_torob": seller.get("price"),
                        "instagram": None,
                        "telegram": None,
                        "whatsapp": None,
                        "crawl_status": "not_crawled",
                    }
                    if cfg.CRAWL_SELLER_SITES:
                        crawl_result = await self.crawler.crawl(seller.get("seller_url", ""))
                        if crawl_result.get("_debug", {}).get("valid_external_urls", 0):
                            crawler_stats["valid_external_urls"] += 1
                        if crawl_result.get("_debug", {}).get("skipped", 0):
                            crawler_stats["skipped"] += 1
                        if crawl_result.get("store_url"):
                            lead["store_url"] = crawl_result["store_url"]
                        lead.update({k: v for k, v in crawl_result.items() if not k.startswith("_debug")})
                    all_sellers.append(lead)
            except Exception:
                continue

        unique_sellers, duplicate_count = Deduplicator.deduplicate(all_sellers)
        self.db.save_leads(unique_sellers)
        excel_path = self.exporter.export(unique_sellers)
        sync_result = self.sync.sync(unique_sellers)

        summary = {
            "query": query,
            "products_found": len(product_results),
            "seller_candidates": len(all_sellers),
            "unique_sellers": len(unique_sellers),
            "duplicates_removed": duplicate_count,
            "excel_path": excel_path,
            "sync_result": sync_result,
            "crawler_stats": crawler_stats,
            "db_stats": self.db.stats(),
        }
        return summary

    def status(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "config": {
                "headless": cfg.TOROB_HEADLESS,
                "crawl_seller_sites": cfg.CRAWL_SELLER_SITES,
            },
            "db_stats": self.db.stats(),
        }

    def sync_pending(self) -> dict[str, Any]:
        pending = self.db.get_pending_leads()
        sync_result = self.sync.sync(pending)
        if sync_result.get("status") == "ok":
            self.db.mark_lead_synced([lead["id"] for lead in pending if "id" in lead])
        return {"pending_count": len(pending), "sync_result": sync_result}
