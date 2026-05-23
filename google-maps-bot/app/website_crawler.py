# app/website_crawler.py - MVP نهایی (Enrichment Layer)
from playwright.sync_api import sync_playwright
import time
import re
import random
from urllib.parse import urljoin
from datetime import datetime
from app.database import Database
from app.config import Config
from app.utils import accept_cookies

class WebsiteCrawler:
    """
    Website Enrichment Layer MVP
    فقط ایمیل، سوشال، تلفن اضافی، contact/about pages
    """

    def __init__(self):
        self.db = Database()

    # ========== extraction helpers ==========
    def extract_emails(self, content: str) -> list:
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = re.findall(pattern, content)
        return list(set(matches))[:3]  # حداکثر 3 ایمیل

    def extract_instagram(self, content: str) -> str:
        patterns = [
            r'instagram\.com/([a-zA-Z0-9_.]+)',
            r'instagr\.am/([a-zA-Z0-9_.]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return f"instagram.com/{match.group(1)}"
        return ""

    def extract_telegram(self, content: str) -> str:
        patterns = [
            r't\.me/([a-zA-Z0-9_]+)',
            r'telegram\.me/([a-zA-Z0-9_]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return f"t.me/{match.group(1)}"
        return ""

    def extract_whatsapp(self, content: str) -> str:
        match = re.search(r'wa\.me/(\d+)', content)
        return f"wa.me/{match.group(1)}" if match else ""

    def extract_extra_phones(self, content: str, main_phone: str = "") -> str:
        """شماره‌های اضافی (غیر از شماره اصلی گوگل مپ)"""
        pattern = r'09\d{9}|0\d{10}'
        matches = re.findall(pattern, content)
        unique = list(set(matches))
        if main_phone and main_phone in unique:
            unique.remove(main_phone)
        return ",".join(unique[:3])  # حداکثر 3 تا

    # ========== single business crawl ==========
    def crawl_business(self, page, business) -> dict:
        result = {
            'email': '',
            'instagram': '',
            'telegram': '',
            'whatsapp': '',
            'extra_phones': '',
            'contact_page_url': '',
            'about_page_url': '',
            'crawl_status': 'failed',
            'crawl_error': ''
        }

        website_url = business['website']
        if not website_url or 'google.com' in website_url:
            result['crawl_error'] = 'Invalid or google URL'
            return result

        try:
            print(f"  🌐 Crawling: {website_url}")

            # صفحه اصلی
            page.goto(website_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            content = page.content()

            emails = self.extract_emails(content)
            result['email'] = emails[0] if emails else ''
            result['instagram'] = self.extract_instagram(content)
            result['telegram'] = self.extract_telegram(content)
            result['whatsapp'] = self.extract_whatsapp(content)

            # صفحات تماس و درباره
            paths = ['/contact', '/contact-us', '/about', '/about-us', '/تماس-با-ما', '/درباره-ما']
            for path in paths:
                try:
                    full_url = urljoin(website_url, path)
                    page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
                    time.sleep(1.5)
                    content = page.content()

                    if 'contact' in path or 'تماس' in path:
                        result['contact_page_url'] = full_url
                    if 'about' in path or 'درباره' in path:
                        result['about_page_url'] = full_url

                    if not result['email']:
                        emails2 = self.extract_emails(content)
                        result['email'] = emails2[0] if emails2 else ''
                    if not result['instagram']:
                        result['instagram'] = self.extract_instagram(content)
                    if not result['telegram']:
                        result['telegram'] = self.extract_telegram(content)
                    if not result['whatsapp']:
                        result['whatsapp'] = self.extract_whatsapp(content)

                except Exception as e:
                    continue

            # استخراج شماره‌های اضافی (از کل محتوا)
            all_content = page.content()
            result['extra_phones'] = self.extract_extra_phones(all_content)
            result['crawl_status'] = 'done'

        except Exception as e:
            result['crawl_error'] = f"{type(e).__name__}: {str(e)[:100]}"
            print(f"  ⚠️ Crawl error: {result['crawl_error']}")

        return result

    # ========== main runner ==========
    def run(self, limit: int = None):
        print("=" * 60)
        print("📍 Website Crawler MVP (Enrichment Layer)")
        print("=" * 60)

        if limit is None:
            limit = Config.MAX_WEBSITES_TO_CRAWL
            print(f"📋 Using limit from Config: {limit}")

        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, website FROM businesses
                WHERE website != '' AND website IS NOT NULL
                AND status = 'done'
                ORDER BY id
                LIMIT ?
            ''', (limit,))
            businesses = [dict(row) for row in cursor.fetchall()]

        print(f"📋 Found {len(businesses)} businesses with website")

        if not businesses:
            print("⚠️ No businesses with website found!")
            return

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=Config.HEADLESS,
                slow_mo=Config.SLOW_MO
            )
            page = browser.new_page()
            accept_cookies(page)

            for idx, biz in enumerate(businesses, 1):
                print(f"\n🔍 [{idx}/{len(businesses)}] {biz['name'][:50]}...")
                print(f"   Website: {biz['website']}")

                result = self.crawl_business(page, biz)

                if result['email']:
                    print(f"  📧 {result['email']}")
                if result['instagram']:
                    print(f"  📷 {result['instagram']}")
                if result['extra_phones']:
                    print(f"  📞 extra: {result['extra_phones']}")

                # ذخیره در دیتابیس
                self._save_extraction(biz['id'], result)

                delay = random.uniform(*Config.DELAY_BETWEEN_BUSINESSES)
                print(f"  ⏱️ Waiting {delay:.1f}s...")
                time.sleep(delay)

            browser.close()

        self.db.close()
        print("\n✅ Website crawling MVP completed!")

    # ========== save to database ==========
    def _save_extraction(self, business_id: int, data: dict):
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO website_extractions
                (business_id, email, instagram, telegram, whatsapp,
                 extra_phones, contact_page_url, about_page_url,
                 crawl_status, crawl_error, crawled_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                business_id,
                data.get('email', ''),
                data.get('instagram', ''),
                data.get('telegram', ''),
                data.get('whatsapp', ''),
                data.get('extra_phones', ''),
                data.get('contact_page_url', ''),
                data.get('about_page_url', ''),
                data.get('crawl_status', 'failed'),
                data.get('crawl_error', ''),
                datetime.now().isoformat()
            ))


if __name__ == "__main__":
    crawler = WebsiteCrawler()
    crawler.run()