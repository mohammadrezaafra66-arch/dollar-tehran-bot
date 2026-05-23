from app.core.base_driver import BaseDriver
from app.core.browser_manager import BrowserManager


class DivarDriver(BaseDriver):
    def __init__(self, headless=True):
        self.browser_manager = BrowserManager(headless=headless)
        self.page = None

    def connect(self):
        self.page = self.browser_manager.start()

    def extract(self, url):
        if not self.page:
            raise RuntimeError('Browser is not connected.')

        self.page.goto(url)

        return {
            'url': url,
            'title': self.page.title()
        }

    def close(self):
        self.browser_manager.close()
