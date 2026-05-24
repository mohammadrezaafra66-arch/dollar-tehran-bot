import asyncio
from datetime import datetime


class PlaywrightBrowserPool:
    def __init__(self):
        self._browsers = {}

    async def register(
        self,
        browser_id: str,
        metadata=None,
    ):
        metadata = metadata or {}

        self._browsers[browser_id] = {
            "metadata": metadata,
            "registered_at": datetime.utcnow().isoformat(),
            "status": "active",
        }

    async def acquire(self, browser_id: str):
        await asyncio.sleep(0)

        return self._browsers.get(browser_id)

    async def release(self, browser_id: str):
        await asyncio.sleep(0)

        browser = self._browsers.get(browser_id)

        if browser:
            browser["status"] = "idle"

    def snapshot(self):
        return dict(self._browsers)
