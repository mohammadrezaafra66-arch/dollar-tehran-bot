from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from playwright.async_api import Page

from afra_market_data.browser.anti_detection import AntiDetection


@dataclass
class TorobSearchResult:
    query: str
    search_url: str
    page_title: str
    product_links: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            'query': self.query,
            'search_url': self.search_url,
            'page_title': self.page_title,
            'product_links': self.product_links,
        }


class TorobSearchService:
    BASE_URL = 'https://torob.com'

    def build_search_url(self, query: str) -> str:
        encoded_query = quote_plus(query.strip())
        return f'{self.BASE_URL}/search/?query={encoded_query}'

    async def search(self, page: Page, query: str) -> TorobSearchResult:
        search_url = self.build_search_url(query)

        await page.goto(search_url, wait_until='domcontentloaded')
        await AntiDetection.random_delay(2.0, 4.0)
        await AntiDetection.human_mouse_move(page)
        await AntiDetection.human_scroll(page)

        title = await page.title()
        product_links = await self.extract_product_links(page)

        return TorobSearchResult(
            query=query,
            search_url=search_url,
            page_title=title,
            product_links=product_links,
        )

    async def extract_product_links(self, page: Page) -> list[str]:
        links = await page.eval_on_selector_all(
            'a[href]',
            '''elements => elements
                .map(element => element.href)
                .filter(href => href.includes('/p/'))
            ''',
        )

        unique_links = []
        seen = set()

        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links
