from app.core.base_plugin import BasePlugin
from app.plugins.divar.driver import DivarDriver


class DivarPlugin(BasePlugin):
    name = 'divar'

    def __init__(self):
        self.driver = DivarDriver()

    def start(self):
        self.driver.connect()

    def stop(self):
        self.driver.close()

    def extract(self, url):
        return self.driver.extract(url)
