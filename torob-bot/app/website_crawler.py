import re
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import cfg


class WebsiteCrawler:
    def __init__(self) -> None:
        self.timeout = cfg.SELLER_CRAWL_TIMEOUT

    async def crawl(self, seller_url: str) -> dict[str, Any]:
        if not seller_url:
            return self._empty_result("skip")

        if seller_url.startswith("http://") or seller_url.startswith("https://"):
            parsed = seller_url
        else:
            parsed = f"https://{seller_url}"

        result = self._empty_result("ok")
        visited = 0
        skipped = 0
        valid_external = 0

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(parsed, follow_redirects=True)
                visited += 1
                final_url = str(response.url)
                if response.status_code < 400 and self._is_external(final_url):
                    valid_external += 1
                    result["store_url"] = final_url
                    text = response.text
                    result["phone"] = result["phone"] or self._extract_phone(text)
                    result["email"] = result["email"] or self._extract_email(text)
                    result["instagram"] = result["instagram"] or self._extract_instagram(text)
                    result["telegram"] = result["telegram"] or self._extract_telegram(text)
                    result["whatsapp"] = result["whatsapp"] or self._extract_whatsapp(text)
                else:
                    skipped += 1
            except Exception:
                skipped += 1

        result["crawl_status"] = "ok" if valid_external else "skip"
        result["_debug"] = {"visited": visited, "skipped": skipped, "valid_external_urls": valid_external, "base_url": parsed}
        return result

    def _is_external(self, url: str) -> bool:
        if not url:
            return False
        host = urlparse(url).netloc.lower()
        return bool(host) and "torob.com" not in host and not host.startswith("api.")

    def _empty_result(self, status: str) -> dict[str, Any]:
        return {
            "phone": None,
            "email": None,
            "instagram": None,
            "telegram": None,
            "whatsapp": None,
            "crawl_status": status,
        }

    def _extract_phone(self, text: str) -> str | None:
        match = re.search(r"09\d{9}", text)
        return match.group(0) if match else None

    def _extract_email(self, text: str) -> str | None:
        match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        return match.group(0) if match else None

    def _extract_instagram(self, text: str) -> str | None:
        match = re.search(r"https?://(?:www\.)?instagram\.com/[^\s\"']+", text, re.I)
        return match.group(0) if match else None

    def _extract_telegram(self, text: str) -> str | None:
        match = re.search(r"https?://t\.me/[^\s\"']+", text, re.I)
        return match.group(0) if match else None

    def _extract_whatsapp(self, text: str) -> str | None:
        match = re.search(r"https?://wa\.me/[^\s\"']+", text, re.I)
        return match.group(0) if match else None
