from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright


@dataclass
class BrowserSettings:
    headless: bool = False
    slow_mo: int = 300
    proxy: Optional[dict[str, str]] = None
    user_agent: Optional[str] = None
    viewport_width: int = 1366
    viewport_height: int = 768


class BrowserManager:
    def __init__(self, settings: BrowserSettings | None = None):
        self.settings = settings or BrowserSettings()
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.settings.headless,
            slow_mo=self.settings.slow_mo,
            proxy=self.settings.proxy,
        )
        self.context = await self.browser.new_context(
            user_agent=self.settings.user_agent,
            viewport={
                'width': self.settings.viewport_width,
                'height': self.settings.viewport_height,
            },
        )

    async def new_page(self) -> Page:
        if not self.context:
            await self.start()
        assert self.context is not None
        return await self.context.new_page()

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
