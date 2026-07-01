# app/main_orchestrator.py - Phase 4 (browser reuse across queries)
import random
import time

from playwright.sync_api import sync_playwright

from app.config import Config
from app.database import Database
from app.query_generator import QueryGenerator
from app.search_collector import SearchCollector
from app.result_extractor import ResultExtractor
from app.website_crawler import WebsiteCrawler


class Orchestrator:
    def __init__(self):
        self.db = Database()
        self.collector = SearchCollector()
        self.extractor = ResultExtractor()

    def run(self):
        # ============================================================
        # Phase 1: Query Generation
        # ============================================================
        print("\n" + "=" * 60)
        print("Phase 1: Query Generation")
        print("=" * 60)
        if Config.is_phase_enabled('Search Collector'):
            QueryGenerator(Config.QUERIES_FILE).run()
        else:
            print("⏭️ Skipped")

        # ============================================================
        # Phase 2: Search — یک browser برای همه query‌ها
        # ============================================================
        print("\n" + "=" * 60)
        print("Phase 2: Search Collection + Enrichment")
        print("=" * 60)
        if Config.is_phase_enabled('Search Collector'):
            pending = self.db.get_pending_queries()
            print(f"📋 {len(pending)} pending queries")

            if pending:
                with sync_playwright() as p:
                    page, browser, context = self.collector.create_page(p)
                    print("🌐 Browser opened — reusing for all queries")

                    # گرم کردن: یه بار به google.com برو
                    try:
                        page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=15000)
                        time.sleep(3)
                        self.collector._accept_cookies(page)
                        print("✅ Browser warmed up")
                    except Exception as e:
                        print(f"⚠️ Warmup failed: {e}")

                    for idx, q in enumerate(pending):
                        query_id   = q['id']
                        query_text = q['query_text']
                        source     = self.db.get_source(q.get('source_id')) if q.get('source_id') else {}

                        print(f"\n🔍 [{query_id}] {query_text}")
                        raw_results = self.collector.collect_on_page(
                            page, query_text,
                            city=source.get('city', ''),
                            province=source.get('province', ''),
                        )

                        if not raw_results:
                            print("  ⚠️ No results")
                            self.db.mark_query_done(query_id)
                        else:
                            enriched = self.extractor.enrich_batch(raw_results)
                            self.db.add_results_batch(query_id, enriched)
                            self.db.mark_query_businesses_done(query_id)
                            self.db.mark_query_done(query_id)
                            print(f"  📊 {self.db.get_stats()}")

                        if idx < len(pending) - 1:
                            delay = random.uniform(*Config.DELAY_BETWEEN_QUERIES)
                            print(f"  ⏳ {delay:.0f}s before next query...")
                            time.sleep(delay)

                    context.close()
                    if browser:
                        browser.close()
                    print("\n✅ Browser closed")
        else:
            print("⏭️ Skipped")

        # ============================================================
        # Phase 3: Website Crawl
        # ============================================================
        print("\n" + "=" * 60)
        print("Phase 3: Website Crawl")
        print("=" * 60)
        if Config.is_phase_enabled('Website Crawler') and Config.WEBSITE_CRAWL_ENABLED:
            WebsiteCrawler().run()
        else:
            print("⏭️ Skipped")

        print("\n✅ Orchestrator finished")
        print(f"Final stats: {self.db.get_stats()}")
