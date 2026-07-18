from __future__ import annotations

import logging
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from app.listing_crawler import DivarListingCrawler, DivarListingCrawlerSettings
from app.detail_extractor import DivarDetailExtractor
from app.anti_ban_throttling import AdaptiveAntiBanThrottler
from app.deduplicator import LeadDeduplicator
from app.deepseek_analyzer import DeepSeekAnalyzer
from app.excel_exporter import export_to_excel
from app.divar_chat import DivarChatMessenger
from app.database import CREATE_LEADS_TABLE, CREATE_SEND_LOG_TABLE, CREATE_CHECKPOINT_TABLE

logger = logging.getLogger(__name__)

import json as _json

def save_checkpoint(db_path: str, url: str, processed_urls: list) -> None:
    import sqlite3, json
    conn = sqlite3.connect(db_path)
    conn.execute("""
        INSERT INTO divar_checkpoints (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
    """, (f"progress:{url}", json.dumps(processed_urls)))
    conn.commit()
    conn.close()


def load_checkpoint(db_path: str, url: str) -> list:
    import sqlite3, json
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT value FROM divar_checkpoints WHERE key=?",
        (f"progress:{url}",)
    ).fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return []



DB_PATH = os.getenv("DIVAR_DB_PATH", "data/divar_leads.db")
MAX_ADS = int(os.getenv("DIVAR_MAX_ADS_PER_RUN", "200"))


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_LEADS_TABLE)
    conn.execute(CREATE_SEND_LOG_TABLE)
    conn.execute(CREATE_CHECKPOINT_TABLE)
    conn.commit()
    conn.close()


def save_leads(leads: list) -> int:
    conn = sqlite3.connect(DB_PATH)
    saved = 0
    for lead in leads:
        try:
            conn.execute("""
                INSERT INTO divar_leads
                (source_url, title, price_text, description,
                 seller_name, phone, city, district, published_at, extraction_status)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(source_url) DO UPDATE SET
                    title = excluded.title,
                    price_text = CASE WHEN excluded.price_text != '' THEN excluded.price_text ELSE divar_leads.price_text END,
                    description = excluded.description,
                    seller_name = CASE WHEN excluded.seller_name != '' THEN excluded.seller_name ELSE divar_leads.seller_name END,
                    phone = CASE WHEN excluded.phone != '' THEN excluded.phone ELSE divar_leads.phone END,
                    city = CASE WHEN excluded.city != '' THEN excluded.city ELSE divar_leads.city END,
                    district = CASE WHEN excluded.district != '' THEN excluded.district ELSE divar_leads.district END,
                    published_at = excluded.published_at,
                    extraction_status = excluded.extraction_status,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                lead.get("source_url", ""),
                lead.get("title", ""),
                lead.get("price_text", ""),
                lead.get("description", ""),
                lead.get("seller_name", ""),
                lead.get("phone", ""),
                lead.get("city", ""),
                lead.get("district", ""),
                lead.get("published_at_text", ""),
                lead.get("extraction_status", "ok"),
            ))
            saved += 1
        except Exception as exc:
            logger.debug(f"DB insert skip: {exc}")
    conn.commit()
    conn.close()
    return saved


def load_leads_for_ai() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, title, price_text, description, city, seller_name
        FROM divar_leads
        WHERE ai_analyzed = 0 AND extraction_status = 'ok'
        LIMIT 100
    """).fetchall()
    conn.close()
    return [
        {"id": r[0], "title": r[1], "price_text": r[2],
         "description": r[3], "city": r[4], "seller_name": r[5]}
        for r in rows
    ]


def save_ai_analysis(lead_id: int, analysis: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE divar_leads SET ai_analysis=?, ai_analyzed=1 WHERE id=?",
                 (analysis, lead_id))
    conn.commit()
    conn.close()


def load_leads_for_messaging() -> list:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, source_url, seller_name, title, city, phone
        FROM divar_leads
        WHERE message_sent = 0 AND extraction_status = 'ok' AND phone != ''
        ORDER BY id LIMIT 50
    """).fetchall()
    conn.close()
    return [
        {"id": r[0], "source_url": r[1], "seller_name": r[2],
         "title": r[3], "city": r[4], "phone": r[5]}
        for r in rows
    ]


class DivarPipeline:

    def __init__(self) -> None:
        self.throttler = AdaptiveAntiBanThrottler()
        self.deduplicator = LeadDeduplicator()
        self.analyzer = DeepSeekAnalyzer()
        init_db()

    def run(self, listing_url: str, send_messages: bool = False, run_ai: bool = True) -> dict:
        import time
        stats = {
            "discovered": 0, "extracted": 0, "saved": 0,
            "ai_analyzed": 0, "messages_sent": 0, "messages_failed": 0,
            "started_at": datetime.now().isoformat(),
        }
        profile_dir = os.getenv("DIVAR_PROFILE_DIR", "runtime/profiles/divar")
        profile_path = Path(profile_dir) / "default"
        profile_path.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(profile_path),
                channel="msedge",
                proxy={"server": os.getenv("HTTP_PROXY", "")} if os.getenv("HTTP_PROXY", "") else None,
                headless=False,
                slow_mo=200,
                locale="fa-IR",
                timezone_id="Asia/Tehran",
            )
            page = context.new_page()
            logger.info(f"مرحله ۱: جمع‌آوری آگهی‌ها از {listing_url}")
            crawler = DivarListingCrawler(
                DivarListingCrawlerSettings(max_ads=MAX_ADS, max_scrolls=15)
            )
            result = crawler.crawl(page, listing_url)
            stats["discovered"] = len(result.ads)
            logger.info(f"   {stats['discovered']} آگهی پیدا شد")
            logger.info("مرحله ۲: استخراج اطلاعات فروشندگان")
            extractor = DivarDetailExtractor()
            raw_leads = []
            for ad in result.ads:
                detail = extractor.extract(page, ad.url)
                lead_dict = detail.to_dict()
                lead_dict["source_url"] = ad.url
                raw_leads.append(lead_dict)
                stats["extracted"] += 1
                if detail.extraction_status == "ok":
                    self.throttler.record_success("main")
                else:
                    self.throttler.record_failure("main")
                decision = self.throttler.decide("main")
                if decision.pause_seconds > 0:
                    logger.info(f"توقف {decision.pause_seconds}ثانیه: {decision.reason}")
                    time.sleep(decision.pause_seconds)
            page.close()
            context.close()
        logger.info("مرحله ۳: حذف تکراری‌ها و ذخیره")
        dedup_result = self.deduplicator.deduplicate(raw_leads)
        unique = dedup_result.unique_leads
        stats["saved"] = save_leads(unique)
        logger.info(f"   {stats['saved']} رکورد ذخیره شد")
        if run_ai:
            logger.info("مرحله ۴: تحلیل DeepSeek")
            for lead in load_leads_for_ai():
                analysis = self.analyzer.analyze(lead)
                if analysis:
                    save_ai_analysis(lead["id"], analysis)
                    stats["ai_analyzed"] += 1
            logger.info(f"   {stats['ai_analyzed']} رکورد تحلیل شد")
        logger.info("مرحله ۵: ساخت خروجی Excel")
        export_to_excel(DB_PATH)
        if send_messages:
            logger.info("مرحله ۶: ارسال پیام‌ها")
            messenger = DivarChatMessenger()
            msg_stats = messenger.run_campaign(load_leads_for_messaging())
            stats["messages_sent"] = msg_stats["sent"]
            stats["messages_failed"] = msg_stats["failed"]
            logger.info(f"   {stats['messages_sent']} پیام ارسال شد")
        stats["finished_at"] = datetime.now().isoformat()
        return stats

