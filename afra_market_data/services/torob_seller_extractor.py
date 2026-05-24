from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from playwright.async_api import Page


@dataclass
class TorobSellerSnapshot:
    product_url: str
    seller_name: str
    price_text: str
    warranty_text: str
    seller_url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'product_url': self.product_url,
            'seller_name': self.seller_name,
            'price_text': self.price_text,
            'warranty_text': self.warranty_text,
            'seller_url': self.seller_url,
        }


class TorobSellerExtractor:
    async def extract(self, page: Page, product_url: str) -> list[TorobSellerSnapshot]:
        text = await self._safe_body_text(page)
        links = await self._safe_links(page)

        price_candidates = self._extract_price_candidates(text)
        seller_links = [link for link in links if 'shop' in link or 'seller' in link or 'store' in link]

        snapshots: list[TorobSellerSnapshot] = []

        for index, price_text in enumerate(price_candidates[:10]):
            snapshots.append(
                TorobSellerSnapshot(
                    product_url=product_url,
                    seller_name=f'unknown_seller_{index + 1}',
                    price_text=price_text,
                    warranty_text='',
                    seller_url=seller_links[index] if index < len(seller_links) else '',
                )
            )

        return snapshots

    async def _safe_body_text(self, page: Page) -> str:
        try:
            return await page.locator('body').inner_text(timeout=5000)
        except Exception:
            return ''

    async def _safe_links(self, page: Page) -> list[str]:
        try:
            return await page.eval_on_selector_all(
                'a[href]',
                'elements => elements.map(element => element.href)',
            )
        except Exception:
            return []

    def _extract_price_candidates(self, text: str) -> list[str]:
        normalized = text.replace(',', '').replace('٬', '').replace('تومان', ' تومان')
        matches = re.findall(r'\d{5,}\s*تومان', normalized)

        unique: list[str] = []
        seen = set()

        for match in matches:
            value = match.strip()
            if value not in seen:
                seen.add(value)
                unique.append(value)

        return unique
