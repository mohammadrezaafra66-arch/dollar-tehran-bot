import asyncio
import random
import re
from typing import Any
from urllib.parse import quote

import httpx

from app.config import cfg


class TorobScraper:
    def __init__(self) -> None:
        self.base_url = "https://torob.com"
        self.api_base = "https://api.torob.com/v4/base-product/details/"

    async def search_products(self, query: str) -> list[dict[str, Any]]:
        search_url = f"{self.base_url}/search/?query={quote(query.strip())}"
        html = await self._fetch_text(search_url)
        if not html:
            return []
        prks = self._extract_prks(html)
        search_id = self._extract_param(html, "search_id")
        suid = self._extract_param(html, "suid")

        products = []
        for prk in prks[:8]:
            detail = await self._fetch_product_detail(prk, search_id, suid)
            if not detail:
                continue
            name = detail.get("name1") or detail.get("name2") or ""
            products.append(
                {
                    "query": query,
                    "prk": prk,
                    "name": name,
                    "url": self._build_product_url(prk, name),
                }
            )
        return products

    async def extract_sellers(self, product_url: str) -> list[dict[str, Any]]:
        prk = self._extract_prk(product_url)
        if not prk:
            return []

        detail = await self._fetch_product_detail(prk)
        if not detail:
            return []

        sellers = []
        for item in detail.get("products_info", {}).get("result", []) or []:
            sellers.append(
                {
                    "name": item.get("shop_name") or item.get("name1") or "unknown",
                    "price": int(item.get("price") or 0),
                    "seller_url": item.get("page_url") or product_url,
                    "torob_url": product_url,
                }
            )
        return sellers[: cfg.TOROB_MAX_SELLERS]

    async def _fetch_text(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
        except Exception:
            return ""

    async def _fetch_product_detail(self, prk: str, search_id: str | None = None, suid: str | None = None) -> dict[str, Any] | None:
        params = [
            "source=next_desktop",
            "discover_method=search",
            "algorithm=result_adv",
            f"prk={prk}",
            "rank=0",
        ]
        if search_id:
            params.append(f"search_id={search_id}")
        if suid:
            params.append(f"init_suid={suid}")
        url = f"{self.api_base}?{'&'.join(params)}"
        try:
            async with httpx.AsyncClient(timeout=30, headers={"User-Agent": "Mozilla/5.0"}) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload = response.json()
                return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    def _extract_prks(self, html: str) -> list[str]:
        prks = re.findall(r"prk=([a-zA-Z0-9\-]+)", html)
        seen = set()
        unique = []
        for prk in prks:
            if prk not in seen:
                seen.add(prk)
                unique.append(prk)
        return unique

    def _extract_param(self, html: str, key: str) -> str | None:
        match = re.search(rf"{key}=([a-zA-Z0-9\-]+)", html)
        return match.group(1) if match else None

    def _extract_prk(self, value: str) -> str | None:
        if not value:
            return None
        match = re.search(r"prk=([a-zA-Z0-9\-]+)", value)
        if match:
            return match.group(1)
        if "/p/" in value:
            tail = value.split("/p/", 1)[1]
            candidate = tail.split("/", 1)[0]
            if candidate and re.fullmatch(r"[a-zA-Z0-9\-]{4,}", candidate):
                return candidate
        if re.fullmatch(r"[a-zA-Z0-9\-]{4,}", value):
            return value
        return None

    def _build_product_url(self, prk: str, name: str) -> str:
        slug = re.sub(r"[^\w]+", "-", name).strip("-").lower() or prk
        return f"{self.base_url}/p/{prk}/{slug}"

    async def _delay(self) -> None:
        await asyncio.sleep(random.uniform(cfg.TOROB_MIN_DELAY, cfg.TOROB_MAX_DELAY))
