import asyncio
import json
import random
import re
from typing import Any
from urllib.parse import quote

import httpx
from app.seller_extractor import SellerExtractor

from app.config import cfg


class TorobScraper:
    def __init__(self) -> None:
        self.base_url = "https://torob.com"
        self.user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

    async def search_products(self, query: str) -> list[dict[str, Any]]:
        search_url = f"{self.base_url}/search/?query={quote(query.strip())}"
        try:
            headers = {"User-Agent": self.user_agent, "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"}
            async with httpx.AsyncClient(timeout=30, headers=headers) as client:
                resp = await client.get(search_url)
                resp.raise_for_status()
                html = resp.text

            # try to parse embedded JSON first
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            products: list[dict[str, Any]] = []
            seen = set()
            if m:
                try:
                    data = json.loads(m.group(1))
                    props = data.get("props", {}).get("pageProps", {})
                    # primary search results live under 'products'
                    products_list = props.get("products") or []
                    if not products_list:
                        # fallback to other possible containers
                        products_list = (props.get("vlp_result") or {}).get("result", []) or []

                    for item in products_list[:8]:
                        # try direct prk fields or extract from known URL fields
                        prk = item.get("prk") or item.get("id") or item.get("product_id")
                        if not prk:
                            # try web_client_absolute_url or more_info_url
                            web = item.get("web_client_absolute_url") or item.get("more_info_url") or ""
                            prk = self._extract_prk(web) or (re.search(r"prk=([A-Za-z0-9\-]+)", web) and re.search(r"prk=([A-Za-z0-9\-]+)", web).group(1))
                        if not prk:
                            continue
                        name = item.get("name1") or item.get("name2") or item.get("title") or ""
                        # prefer client path if present
                        web_path = item.get("web_client_absolute_url")
                        if web_path and web_path.startswith("/p/"):
                            url = f"{self.base_url}{web_path}"
                        else:
                            url = f"{self.base_url}/p/{prk}"
                        if url in seen:
                            continue
                        seen.add(url)
                        products.append({"query": query, "prk": prk, "name": name, "url": url})
                except Exception:
                    pass

            # fallback: extract anchors from HTML
            if not products:
                hrefs = re.findall(r'href="(/p/[A-Za-z0-9\-]+)"', html)
                for href in hrefs:
                    if href in seen:
                        continue
                    seen.add(href)
                    prk = self._extract_prk(href)
                    name = href.split("/")[-1]
                    products.append({"query": query, "prk": prk or "", "name": name, "url": f"{self.base_url}{href}"})

            await self._delay()
            return products
        except Exception:
            return []

    async def extract_sellers(self, product_url: str) -> list[dict[str, Any]]:
        if not product_url:
            return []

        if not product_url.startswith("http"):
            # accept raw prk, '/p/...' path, or relative url
            prk = self._extract_prk(product_url)
            if prk and (not product_url.startswith("/p/")):
                product_url = f"{self.base_url}/p/{prk}"
            else:
                product_url = f"{self.base_url}{product_url}"

        try:
            headers = {"User-Agent": self.user_agent, "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7"}
            async with httpx.AsyncClient(timeout=30, headers=headers) as client:
                resp = await client.get(product_url)
                resp.raise_for_status()
                html = resp.text

            payload = None
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if m:
                try:
                    payload = json.loads(m.group(1))
                except Exception:
                    payload = None

            sellers = SellerExtractor().parse(payload, product_url)
            await self._delay()
            return sellers
        except Exception:
            return []

    def _parse_sellers(self, payload: dict[str, Any], product_url: str) -> list[dict[str, Any]]:
        page_props = payload.get("props", {}).get("pageProps", {})
        product_data = page_props.get("baseProduct") or page_props.get("product") or {}
        products_info = product_data.get("products_info", {}) or {}
        result = products_info.get("result", []) or []

        sellers: list[dict[str, Any]] = []
        for item in result[: cfg.TOROB_MAX_SELLERS]:
            sellers.append(
                {
                    "name": item.get("shop_name") or item.get("name1") or item.get("name2") or "unknown",
                    "price": int(item.get("price") or 0),
                    "seller_url": item.get("page_url") or product_url,
                    "torob_url": product_url,
                }
            )
        return sellers

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

    async def _delay(self) -> None:
        await asyncio.sleep(random.uniform(2.0, 5.0))
