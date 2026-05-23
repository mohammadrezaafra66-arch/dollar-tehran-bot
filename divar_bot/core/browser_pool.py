from queue import Queue
from threading import Lock

from divar_bot.core.browser_manager import BrowserManager


class BrowserPool:
    def __init__(self, size=2, headless=True):
        self.size = size
        self.headless = headless
        self.pool = Queue(maxsize=size)
        self.lock = Lock()
        self._initialized = False

    def initialize(self):
        with self.lock:
            if self._initialized:
                return

            for _ in range(self.size):
                browser = BrowserManager(headless=self.headless)
                self.pool.put(browser)

            self._initialized = True

    def acquire(self):
        self.initialize()
        return self.pool.get()

    def release(self, browser):
        self.pool.put(browser)
