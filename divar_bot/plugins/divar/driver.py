from divar_bot.core.base_driver import BaseDriver
from divar_bot.core.browser_manager import BrowserManager


class DivarDriver(BaseDriver):
    def __init__(self, headless=True):
        self.browser_manager = BrowserManager(headless=headless)
        self.page = None

    def connect(self):
        self.page = self.browser_manager.start()

    def extract(self, url):
        if not self.page:
            raise RuntimeError('Browser is not connected.')

        if hasattr(self.page, 'goto'):
            self.page.goto(url)
            title = self.page.title()
        else:
            title = 'browser_not_available'

        return {
            'url': url,
            'title': title
        }

    def close(self):
        self.browser_manager.close()
