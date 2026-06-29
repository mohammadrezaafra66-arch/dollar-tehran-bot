# website_crawler.py - نسخه سبک با httpx (بدون Playwright)
import httpx
import re
import time
import random
from urllib.parse import urljoin
from app.database import Database
from app.config import Config
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fa,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/about", "/about-us",
    "/تماس-با-ما", "/درباره-ما", "/ارتباط-با-ما",
]


class WebsiteCrawler:
    def __init__(self):
        self.db = Database()

    def _extract_emails(self, text: str) -> str:
        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        valid = [e for e in set(found) if not any(x in e for x in ['noreply', 'no-reply', 'example'])]
        return ", ".join(valid[:3])

    def _extract_instagram(self, text: str) -> str:
        m = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)', text)
        return f"instagram.com/{m.group(1)}" if m else ""

    def _extract_telegram(self, text: str) -> str:
        m = re.search(r't\.me/([a-zA-Z0-9_]+)', text)
        return f"t.me/{m.group(1)}" if m else ""

    def _extract_whatsapp(self, text: str) -> str:
        m = re.search(r'wa\.me/(\d+)', text)
        return f"wa.me/{m.group(1)}" if m else ""

    def _extract_phones(self, text: str, main_phone: str = "") -> str:
        found = re.findall(r'09\d{9}|0\d{10}', text)
        unique = list(set(found))
        if main_phone in unique:
            unique.remove(main_phone)
        return ", ".join(unique[:3])

    def _fetch(self, url: str, timeout: int = 15) -> str:
        try:
            with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=timeout) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    return resp.text
        except Exception as e:
            logger.debug(f"Fetch failed for {url}: {e}")
        return ""

    def _crawl_one(self, website: str, main_phone: str = "") -> dict:
        result = {
            "email": "", "instagram": "", "telegram": "",
            "whatsapp": "", "extra_phones": "",
            "contact_page_url": "", "crawl_status": "failed"
        }

        if not website or "google.com" in website:
            return result

        main_html = self._fetch(website)
        if not main_html:
            return result

        all_text = main_html

        for path in CONTACT_PATHS:
            contact_url = urljoin(website, path)
            contact_html = self._fetch(contact_url, timeout=10)
            if contact_html:
                all_text += " " + contact_html
                result["contact_page_url"] = contact_url
                break

        result["email"] = self._extract_emails(all_text)
        result["instagram"] = self._extract_instagram(all_text)
        result["telegram"] = self._extract_telegram(all_text)
        result["whatsapp"] = self._extract_whatsapp(all_text)
        result["extra_phones"] = self._extract_phones(all_text, main_phone)
        result["crawl_status"] = "done"

        return result

    def run(self):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.id, b.website, b.phone
                FROM businesses b
                LEFT JOIN website_extractions w ON w.business_id = b.id
                WHERE b.status = "done"
                  AND w.id IS NULL
                  AND b.website IS NOT NULL
                  AND b.website != ""
                LIMIT ?
            ''', (Config.MAX_WEBSITES_TO_CRAWL,))
            businesses = cursor.fetchall()

        if not businesses:
            print("✅ No websites to crawl")
            return

        print(f"🌐 Crawling {len(businesses)} websites with httpx...")

        for biz_id, website, phone in businesses:
            print(f"  → {website}")
            result = self._crawl_one(website, phone or "")

            with self.db._get_connection() as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO website_extractions
                    (business_id, email, instagram, telegram, whatsapp,
                     extra_phones, contact_page_url, crawl_status, extracted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime("now"))
                ''', (
                    biz_id,
                    result["email"], result["instagram"],
                    result["telegram"], result["whatsapp"],
                    result["extra_phones"], result["contact_page_url"],
                    result["crawl_status"]
                ))

            time.sleep(random.uniform(2.0, 5.0))

        print("✅ Website crawling done")
