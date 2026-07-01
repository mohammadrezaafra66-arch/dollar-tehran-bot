# app/main_orchestrator.py - Phase 4
import random
import time

from app.config import Config
from app.database import Database
from app.query_generator import QueryGenerator
from app.search_collector import SearchCollector
from app.result_extractor import ResultExtractor
from app.website_crawler import WebsiteCrawler


class Orchestrator:
    """
    Phase 1: QueryGenerator   → generated_queries (pending)
    Phase 2: SearchCollector  → businesses (pending) + ResultExtractor (in-memory enrich)
    Phase 3: WebsiteCrawler   → website_extractions
    """

    def __init__(self):
        self.db = Database()
        self.collector = SearchCollector()
        self.extractor = ResultExtractor()

    def run(self):
        # ============================================================
        # Phase 1: تولید کوئری از Excel
        # ============================================================
        print("\n" + "=" * 60)
        print("Phase 1: Query Generation")
        print("=" * 60)
        if Config.is_phase_enabled('Search Collector'):
            qgen = QueryGenerator(Config.QUERIES_FILE)
            qgen.run()
        else:
            print("⏭️ Skipped (disabled in management file)")

        # ============================================================
        # Phase 2: جستجو + غنی‌سازی + ذخیره
        # ============================================================
        print("\n" + "=" * 60)
        print("Phase 2: Search Collection + Enrichment")
        print("=" * 60)
        if Config.is_phase_enabled('Search Collector'):
            pending = self.db.get_pending_queries()
            print(f"📋 {len(pending)} pending queries")

            for q in pending:
                query_id   = q['id']
                query_text = q['query_text']
                source_id  = q.get('source_id')

                # شهر و استان از source
                source   = self.db.get_source(source_id) if source_id else {}
                city     = source.get('city', '')
                province = source.get('province', '')

                print(f"\n🔍 [{query_id}] {query_text}")

                # collect از گوگل
                raw_results = self.collector.collect(
                    query_text, city=city, province=province
                )

                if not raw_results:
                    print("  ⚠️ No results — skipping")
                    self.db.mark_query_done(query_id)
                    continue

                # غنی‌سازی در حافظه
                enriched = self.extractor.enrich_batch(raw_results)

                # ذخیره در DB
                self.db.add_results_batch(query_id, enriched)

                # تبدیل pending → done تا website_crawler بتونه بگیره
                self.db.mark_query_businesses_done(query_id)
                self.db.mark_query_done(query_id)

                stats = self.db.get_stats()
                print(f"  📊 DB total={stats['total']} done={stats['done']}")

                # تأخیر بین کوئری‌ها
                if q != pending[-1]:
                    delay = random.uniform(*Config.DELAY_BETWEEN_QUERIES)
                    print(f"  ⏳ {delay:.0f}s delay...")
                    time.sleep(delay)
        else:
            print("⏭️ Skipped")

        # ============================================================
        # Phase 3: Crawl وبسایت‌ها
        # ============================================================
        print("\n" + "=" * 60)
        print("Phase 3: Website Crawl")
        print("=" * 60)
        if Config.is_phase_enabled('Website Crawler') and Config.WEBSITE_CRAWL_ENABLED:
            crawler = WebsiteCrawler()
            crawler.run()
        else:
            print("⏭️ Skipped (disabled)")

        print("\n✅ Orchestrator finished")
        print(f"Final stats: {self.db.get_stats()}")
