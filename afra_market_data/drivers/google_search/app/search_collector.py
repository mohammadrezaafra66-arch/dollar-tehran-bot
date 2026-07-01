# app/search_collector.py - Phase 1 (stealth + browser-reuse capable)
import re
import time
import random
import urllib.parse
from typing import List, Dict

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from app.config import Config
from app.browser_factory import launch_chromium, find_local_browser

GOOGLE_SEARCH_URL = "https://www.google.com/search"

# patch webdriver detection


PHONE_RE = re.compile(
    r'(?:'
    r'\+98\s?\d{10}'
    r'|0\d{2,3}[\s\-]\d{7,8}'
    r'|0[1-9]\d{9}'
    r')'
)

ADDRESS_KEYWORDS = [
    'خیابان', 'بلوار', 'کوچه', 'میدان', 'اتوبان',
    'پلاک', 'طبقه', 'پاساژ', 'مجتمع', 'کیلومتر',
]


def _human_delay(min_s: float, max_s: float):
    time.sleep(random.uniform(min_s, max_s))


class SearchCollector:
    """
    collect()          → باز و بسته کردن browser خودش (single call)
    collect_on_page()  → از page موجود استفاده می‌کنه (orchestrator)
    create_page()      → برای orchestrator که browser رو مدیریت می‌کنه
    """

    def collect(self, query_text: str, city: str = '', province: str = '') -> List[Dict]:
        """single-use: browser رو خودش باز و می‌بنده"""
        with sync_playwright() as p:
            page, browser, context = self.create_page(p)
            results = self._run_pages(page, query_text, city, province)
            context.close()
            if browser:
                browser.close()
        return results

    def collect_on_page(self, page, query_text: str, city: str = '', province: str = '') -> List[Dict]:
        """از page موجود استفاده می‌کنه — orchestrator این رو صدا می‌زنه"""
        return self._run_pages(page, query_text, city, province)

    def create_page(self, p):
        """orchestrator این رو مستقیم صدا می‌زنه تا browser رو مدیریت کنه"""
        context_opts = {
            'locale': 'fa-IR',
            'timezone_id': 'Asia/Tehran',
            'user_agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/149.0.0.0 Safari/537.36'
            ),
            'viewport': {'width': 1366, 'height': 768},
        }

        if Config.USE_CHROME_PROFILE and Config.USER_DATA_DIR:
            print(f"  🔑 Chrome profile: {Config.USER_DATA_DIR}")
            local_browser = find_local_browser()
            launch_kwargs = {
                'headless': Config.HEADLESS,
                'slow_mo': Config.SLOW_MO,
                **context_opts,
            }
            if local_browser:
                launch_kwargs['executable_path'] = local_browser
            launch_kwargs['args'] = [
                f'--profile-directory={Config.PROFILE_NAME}',
                '--disable-blink-features=AutomationControlled',
                '--start-maximized',
                '--disable-infobars',
            ]
            context = p.chromium.launch_persistent_context(Config.USER_DATA_DIR, **launch_kwargs)
            browser = None
        else:
            browser = launch_chromium(p)
            context = browser.new_context(**context_opts)

        page = context.new_page()
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => false, configurable: true});
            Object.defineProperty(navigator, 'plugins', {get: () => {const a=[1,2,3,4,5];a.__proto__=PluginArray.prototype;return a;}});
            Object.defineProperty(navigator, 'languages', {get: () => ['fa-IR','fa','en-US','en']});
            window.chrome = {app:{isInstalled:false},runtime:{},webstore:{onInstallStageChanged:{},onDownloadProgress:{}}};
            const origQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (p) => p.name==='notifications' ? Promise.resolve({state:Notification.permission}) : origQuery(p);
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
        """)
        page.set_default_timeout(Config.PAGE_TIMEOUT)
        return page, browser, context

    def _run_pages(self, page, query_text: str, city: str, province: str) -> List[Dict]:
        all_results: List[Dict] = []
        for page_num in range(1, Config.MAX_PAGES_PER_QUERY + 1):
            print(f"  📄 Page {page_num}: {query_text}")
            try:
                url = self._build_url(query_text, page_num)
                page.goto(url, wait_until='domcontentloaded', timeout=Config.PAGE_TIMEOUT)
                _human_delay(2.5, 4.5)

                if self._is_captcha(page):
                    print("  ⚠️ CAPTCHA — waiting 60s for manual solve...")
                    time.sleep(60)
                    if self._is_captcha(page):
                        print("  ❌ Still blocked — aborting query")
                        break

                self._accept_cookies(page)
                results = self._extract_results(page, query_text, city, province)
                all_results.extend(results)
                print(f"  ✅ Page {page_num}: {len(results)} results")

                if len(results) < 5:
                    break
                if page_num < Config.MAX_PAGES_PER_QUERY:
                    delay = random.uniform(*Config.DELAY_BETWEEN_PAGES)
                    print(f"  ⏳ {delay:.0f}s...")
                    time.sleep(delay)

            except PlaywrightTimeout:
                print(f"  ⚠️ Timeout page {page_num}")
                break
            except Exception as e:
                print(f"  ❌ Error page {page_num}: {e}")
                break
        return all_results

    def _build_url(self, query_text: str, page_num: int) -> str:
        params = {'q': query_text, 'hl': 'fa', 'gl': 'ir', 'num': '10'}
        if page_num > 1:
            params['start'] = str((page_num - 1) * 10)
        return f"{GOOGLE_SEARCH_URL}?{urllib.parse.urlencode(params)}"

    def _is_captcha(self, page) -> bool:
        try:
            if 'sorry' in page.url or 'captcha' in page.url.lower():
                return True
            for sel in ['#captcha-form', 'form[action*="sorry"]', '#recaptcha']:
                if page.locator(sel).count() > 0:
                    return True
        except Exception:
            pass
        return False

    def _accept_cookies(self, page):
        try:
            for sel in ['button:has-text("Accept all")', 'button:has-text("Reject all")', '[aria-label="Accept all"]']:
                btn = page.locator(sel)
                if btn.count() > 0:
                    btn.first.click()
                    _human_delay(0.8, 1.5)
                    return
        except Exception:
            pass

    def _extract_results(self, page, query_text: str, city: str, province: str) -> List[Dict]:
        results: List[Dict] = []
        try:
            page.wait_for_selector('#rso', timeout=10000)
        except PlaywrightTimeout:
            print("  ⚠️ #rso not found")
            return results

        for h3 in page.query_selector_all('#rso h3')[:Config.MAX_RESULTS_PER_QUERY]:
            try:
                title = (h3.inner_text() or '').strip()
                if not title:
                    continue
                parent_a = h3.evaluate_handle('el => el.closest("a")').as_element()
                if not parent_a:
                    continue
                result_url = self._clean_url(parent_a.get_attribute('href') or '')
                if not result_url:
                    continue
                snippet = phone = address = ''
                g_el = h3.evaluate_handle('el => el.closest(".g")').as_element()
                if g_el:
                    snippet = self._get_snippet(g_el)
                    phone = self._extract_phone(snippet) or self._extract_phone(title)
                    address = self._extract_address(snippet)
                results.append({
                    'name': title, 'result_url': result_url,
                    'result_snippet': snippet[:500], 'phone': phone,
                    'address': address, 'city': city, 'province': province,
                })
            except Exception as e:
                print(f"  ⚠️ Skip: {e}")
        return results

    def _get_snippet(self, g_el) -> str:
        for sel in ['.VwiC3b', '.IsZvec', '[data-sncf="1"]', '.lEBKkf', '.s3v9rd']:
            try:
                el = g_el.query_selector(sel)
                if el:
                    text = (el.inner_text() or '').strip()
                    if text:
                        return text
            except Exception:
                pass
        return ''

    def _clean_url(self, raw_url: str) -> str:
        if not raw_url:
            return ''
        if raw_url.startswith('/url?'):
            params = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
            return params.get('q', [''])[0]
        if raw_url.startswith('http'):
            return raw_url
        return ''

    def _extract_phone(self, text: str) -> str:
        if not text:
            return ''
        m = PHONE_RE.search(text)
        if m:
            phone = re.sub(r'[\s\-]', '', m.group())
            if phone.startswith('+98'):
                phone = '0' + phone[3:]
            return phone
        return ''

    def _extract_address(self, snippet: str) -> str:
        if not snippet:
            return ''
        for line in snippet.split('\n'):
            if any(kw in line for kw in ADDRESS_KEYWORDS):
                return line.strip()
        return ''
