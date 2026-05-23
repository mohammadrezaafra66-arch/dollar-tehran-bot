class BrowserManager:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None

    def start(self):
        return True

    def close(self):
        return True
