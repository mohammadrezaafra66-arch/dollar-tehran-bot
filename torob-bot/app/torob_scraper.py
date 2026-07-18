import asyncio
import random
import re
from typing import Any

from playwright.async_api import async_playwright

from app.config import cfg


class TorobScraper:
    def __init__(self) -> None:
        self.base_url = "https://torob.com"

    async def search_products(self, query: str) -> list[dict[str, Any]]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=cfg.TOROB_HEADLESS)
            page = await browser.new_page()
            try:
                search_url = f"{self.base_url}/search/?query={query.strip()}"
                await page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
                await self._delay()
                await page.mouse.wheel(0, 800)
                await self._delay()
                html = await page.content()
                product_urls = self._extract_product_urls(html)
                return [{"query": query, "url": url} for url in product_urls[:10]]
            finally:
                await browser.close()

    async def extract_sellers(self, product_url: str) -> list[dict[str, Any]]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=cfg.TOROB_HEADLESS)
            page = await browser.new_page()
            try:
                await page.goto(product_url, wait_until="domcontentloaded", timeout=60000)
                await self._delay()
                await page.mouse.wheel(0, 600)
                await self._delay()
                html = await page.content()
                sellers = self._extract_sellers_from_html(html, product_url)
                return sellers[: cfg.TOROB_MAX_SELLERS]
            finally:
                await browser.close()

    def _extract_product_urls(self, html: str) -> list[str]:
        hrefs = re.findall(r'href=["\'](https?://[^"\']+)["\']', html)
        urls = [href for href in hrefs if "/p/" in href and "torob.com" in href]
        seen = set()
        unique = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique.append(url)
        return unique

    def _extract_sellers_from_html(self, html: str, product_url: str) -> list[dict[str, Any]]:
        sellers = []
        for match in re.finditer(r"(?P<name>[^<\n]{1,80})", html):
            text = match.group("name").strip()
            if "تومان" in text or "تومان" in html:
                pass
        price_matches = re.findall(r"(\d{2,12})\s*تومان", html)
        price_candidates = sorted(set(price_matches), key=int)[:10]
        for index, price in enumerate(price_candidates):
            sellers.append(
                {
                    "name": f"seller_{index + 1}",
                    "price": int(price),
                    "seller_url": product_url,
                    "torob_url": product_url,
                }
            )
        return sellers

    async def _delay(self) -> None:
        await asyncio.sleep(random.uniform(cfg.TOROB_MIN_DELAY, cfg.TOROB_MAX_DELAY))
