class BrowserManager:
    def __init__(self, headless=True, slow_mo=0, proxy=None):
        self.headless = headless
        self.slow_mo = slow_mo
        self.proxy = proxy
        self.browser = None
        self.context = None
        self.page = None

    def start(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise RuntimeError('Playwright is not installed. Install it before running browser automation.') from exc

        self.playwright = sync_playwright().start()
        launch_options = {
            'headless': self.headless,
            'slow_mo': self.slow_mo,
        }

        if self.proxy:
            launch_options['proxy'] = {'server': self.proxy}

        self.browser = self.playwright.chromium.launch(**launch_options)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        return self.page

    def close(self):
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
