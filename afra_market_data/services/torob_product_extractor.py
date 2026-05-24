from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page

from afra_market_data.browser.anti_detection import AntiDetection


@dataclass
class TorobProductSnapshot:
    url: str
    title: str
    page_title: str
    raw_text_sample: str
    seller_links: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            'url': self.url,
            'title': self.title,
            'page_title': self.page_title,
            'raw_text_sample': self.raw_text_sample,
            'seller_links': self.seller_links,
        }


class TorobProductExtractor:
    async def extract(self, page: Page, product_url: str) -> TorobProductSnapshot:
        await page.goto(product_url, wait_until='domcontentloaded')
        await AntiDetection.random_delay(2.0, 4.0)
        await AntiDetection.human_mouse_move(page)
        await AntiDetection.human_scroll(page)

        page_title = await page.title()
        title = await self.extract_title(page)
        raw_text_sample = await self.extract_text_sample(page)
        seller_links = await self.extract_seller_links(page)

        return TorobProductSnapshot(
            url=product_url,
            title=title,
            page_title=page_title,
            raw_text_sample=raw_text_sample,
            seller_links=seller_links,
        )

    async def extract_title(self, page: Page) -> str:
        for selector in ['h1', '[data-testid="product-title"]', 'title']:
            try:
                if selector == 'title':
                    return await page.title()
                locator = page.locator(selector).first
                if await locator.count() > 0:
                    text = await locator.inner_text(timeout=3000)
                    if text.strip():
                        return text.strip()
            except Exception:
                continue
        return ''

    async def extract_text_sample(self, page: Page) -> str:
        try:
            text = await page.locator('body').inner_text(timeout=5000)
            return text[:2000]
        except Exception:
            return ''

    async def extract_seller_links(self, page: Page) -> list[str]:
        try:
            links = await page.eval_on_selector_all(
                'a[href]',
                '''elements => elements
                    .map(element => element.href)
                    .filter(href => href.includes('shop') || href.includes('seller') || href.includes('store'))
                ''',
            )
        except Exception:
            links = []

        unique_links = []
        seen = set()
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        return unique_links
